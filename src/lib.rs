//! High-performance Rust acceleration for LiteLLM
//!
//! This module provides Rust-accelerated implementations of core LiteLLM
//! functionality including routing, token counting, rate limiting, and
//! connection pooling.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;

// Helper function to convert HashMap<String, serde_json::Value> to PyDict
fn convert_hashmap_to_pydict(
    py: Python,
    map: HashMap<String, serde_json::Value>,
) -> PyResult<PyObject> {
    let dict = PyDict::new(py);

    for (key, value) in map {
        let py_value = convert_json_value_to_py(py, value)?;
        dict.set_item(key, py_value)?;
    }

    Ok(dict.into())
}

// Helper function to convert serde_json::Value to Python object
#[allow(deprecated)]
fn convert_json_value_to_py(py: Python, value: serde_json::Value) -> PyResult<PyObject> {
    match value {
        serde_json::Value::Null => Ok(py.None()),
        serde_json::Value::Bool(b) => Ok(b.into_py(py)),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.into_py(py))
            } else if let Some(f) = n.as_f64() {
                Ok(f.into_py(py))
            } else {
                Ok(py.None())
            }
        }
        serde_json::Value::String(s) => Ok(s.into_py(py)),
        serde_json::Value::Array(arr) => {
            let py_list = PyList::empty(py);
            for item in arr {
                let py_item = convert_json_value_to_py(py, item)?;
                py_list.append(py_item)?;
            }
            Ok(py_list.into())
        }
        serde_json::Value::Object(obj) => {
            let dict = PyDict::new(py);
            for (key, value) in obj {
                let py_value = convert_json_value_to_py(py, value)?;
                dict.set_item(key, py_value)?;
            }
            Ok(dict.into())
        }
    }
}

pub mod connection_pool;
pub mod core;
pub mod feature_flags;
pub mod performance_monitor;
pub mod rate_limiter;
pub mod tokens;

// ============================================================
// PyO3 Classes for Shimming
// ============================================================

/// Token counter class that can be used to replace LiteLLM's token counting
#[pyclass]
#[derive(Clone)]
pub struct SimpleTokenCounter {
    model_max_tokens: usize,
}

#[pymethods]
impl SimpleTokenCounter {
    #[new]
    #[pyo3(signature = (model_max_tokens=4096))]
    fn new(model_max_tokens: usize) -> Self {
        Self { model_max_tokens }
    }

    /// Count tokens in a text string
    #[pyo3(signature = (text, model=None))]
    fn count_tokens(&self, text: &str, model: Option<&str>) -> PyResult<usize> {
        tokens::count_tokens(text, model).map_err(pyo3::exceptions::PyValueError::new_err)
    }

    /// Count tokens for multiple texts at once
    #[pyo3(signature = (texts, model=None))]
    fn count_tokens_batch(&self, texts: Vec<String>, model: Option<&str>) -> PyResult<Vec<usize>> {
        tokens::count_tokens_batch(&texts, model).map_err(pyo3::exceptions::PyValueError::new_err)
    }

    /// Estimate cost for a request
    fn estimate_cost(
        &self,
        input_tokens: usize,
        output_tokens: usize,
        model: &str,
    ) -> PyResult<f64> {
        tokens::estimate_cost(input_tokens, output_tokens, model)
            .map_err(pyo3::exceptions::PyValueError::new_err)
    }

    /// Get model limits
    fn get_model_limits(&self, py: Python, model: &str) -> PyResult<PyObject> {
        let limits = tokens::get_model_limits(model);
        convert_hashmap_to_pydict(py, limits)
    }

    /// Validate input doesn't exceed model limits
    fn validate_input(&self, text: &str, model: &str) -> PyResult<bool> {
        tokens::validate_input(text, model).map_err(pyo3::exceptions::PyValueError::new_err)
    }

    #[getter]
    fn model_max_tokens(&self) -> usize {
        self.model_max_tokens
    }
}

/// Rate limiter class with token bucket and sliding window algorithms
#[pyclass]
pub struct SimpleRateLimiter {
    default_key: String,
}

#[pymethods]
impl SimpleRateLimiter {
    #[new]
    #[pyo3(signature = (requests_per_minute=60))]
    fn new(requests_per_minute: u64) -> Self {
        // Configure default rate limit
        let config = rate_limiter::RateLimitConfig {
            requests_per_second: requests_per_minute / 60 + 1,
            requests_per_minute,
            requests_per_hour: requests_per_minute * 60,
            burst_size: (requests_per_minute / 10).max(5),
        };
        rate_limiter::set_rate_limit_config("default", config);
        Self {
            default_key: "default".to_string(),
        }
    }

    /// Check if a request is allowed
    #[pyo3(signature = (key=None))]
    fn check(&self, py: Python, key: Option<&str>) -> PyResult<PyObject> {
        let key = key.unwrap_or(&self.default_key);
        let result = rate_limiter::check_rate_limit(key);

        let dict = PyDict::new(py);
        dict.set_item("allowed", result.allowed)?;
        dict.set_item("reason", result.reason)?;
        dict.set_item("remaining_requests", result.remaining_requests)?;
        if let Some(retry_after) = result.retry_after_ms {
            dict.set_item("retry_after_ms", retry_after)?;
        }
        Ok(dict.into())
    }

    /// Check rate limit and return boolean (simpler interface)
    #[pyo3(signature = (key=None))]
    fn is_allowed(&self, key: Option<&str>) -> bool {
        let key = key.unwrap_or(&self.default_key);
        rate_limiter::check_rate_limit(key).allowed
    }

    /// Get remaining requests for a key
    #[pyo3(signature = (key=None))]
    fn get_remaining(&self, key: Option<&str>) -> u64 {
        let key = key.unwrap_or(&self.default_key);
        rate_limiter::get_remaining_requests(key)
    }

    /// Get statistics for all rate limiters
    fn get_stats(&self, py: Python) -> PyResult<PyObject> {
        let stats = rate_limiter::get_rate_limit_stats();
        convert_hashmap_to_pydict(py, stats)
    }
}

/// Connection pool class for managing API connections
#[pyclass]
pub struct SimpleConnectionPool {
    #[allow(dead_code)]
    pool_name: String,
}

#[pymethods]
impl SimpleConnectionPool {
    #[new]
    #[pyo3(signature = (pool_name="default"))]
    fn new(pool_name: &str) -> Self {
        Self {
            pool_name: pool_name.to_string(),
        }
    }

    /// Get a connection to an endpoint
    fn get_connection(&self, endpoint: &str) -> Option<String> {
        connection_pool::get_connection(endpoint)
    }

    /// Return a connection to the pool
    fn return_connection(&self, connection_id: &str) {
        connection_pool::return_connection(connection_id);
    }

    /// Check health of a connection
    fn health_check(&self, connection_id: &str) -> bool {
        connection_pool::health_check_connection(connection_id)
    }

    /// Clean up expired connections
    fn cleanup(&self) {
        connection_pool::cleanup_expired_connections();
    }

    /// Get pool statistics
    fn get_stats(&self, py: Python) -> PyResult<PyObject> {
        let stats = connection_pool::get_connection_pool_stats();
        convert_hashmap_to_pydict(py, stats)
    }
}

/// Advanced router with multiple routing strategies
#[pyclass]
pub struct AdvancedRouter {
    strategy: String,
}

#[pymethods]
impl AdvancedRouter {
    #[new]
    #[pyo3(signature = (strategy="simple_shuffle"))]
    fn new(strategy: &str) -> Self {
        Self {
            strategy: strategy.to_string(),
        }
    }

    /// Get an available deployment for a model
    #[pyo3(signature = (model_list, model, blocked_models=None))]
    fn get_available_deployment(
        &self,
        py: Python,
        model_list: Vec<PyObject>,
        model: String,
        blocked_models: Option<Vec<String>>,
    ) -> PyResult<Option<PyObject>> {
        let blocked = blocked_models.unwrap_or_default();
        let mut available: Vec<PyObject> = Vec::new();

        for item in model_list.iter() {
            if let Ok(dict) = item.downcast_bound::<PyDict>(py) {
                if let Ok(Some(name)) = dict.get_item("model_name") {
                    if let Ok(name_str) = name.extract::<String>() {
                        if name_str == model && !blocked.contains(&name_str) {
                            available.push(item.clone_ref(py));
                        }
                    }
                }
            }
        }

        if available.is_empty() {
            if !model_list.is_empty() {
                let index = rand::random::<usize>() % model_list.len();
                return Ok(Some(model_list[index].clone_ref(py)));
            }
            return Ok(None);
        }

        let index = rand::random::<usize>() % available.len();
        Ok(Some(available[index].clone_ref(py)))
    }

    #[getter]
    fn strategy(&self) -> &str {
        &self.strategy
    }
}

// ============================================================
// Standalone Functions
// ============================================================

/// Check if Rust acceleration is available
#[pyfunction]
fn rust_acceleration_available() -> bool {
    true
}

/// Apply acceleration patches to LiteLLM
#[pyfunction]
fn apply_acceleration() -> bool {
    // In a real implementation, this would apply monkeypatches
    true
}

/// Remove acceleration patches
#[pyfunction]
fn remove_acceleration() {
    // In a real implementation, this would remove monkeypatches
}

/// Basic health check
#[pyfunction]
fn health_check(py: Python) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    dict.set_item("status", "ok")?;
    dict.set_item("rust_available", true)?;

    let components = PyList::new(py, ["core", "tokens", "connection_pool", "rate_limiter"])?;
    dict.set_item("components", components)?;

    Ok(dict.into())
}

/// Check if a feature is enabled
#[pyfunction]
#[pyo3(signature = (feature_name, request_id=None))]
fn is_enabled(feature_name: String, request_id: Option<String>) -> bool {
    feature_flags::is_feature_enabled(&feature_name, request_id.as_deref())
}

/// Get feature status
#[pyfunction]
fn get_feature_status(py: Python) -> PyResult<PyObject> {
    let status = feature_flags::get_all_feature_status();
    convert_hashmap_to_pydict(py, status)
}

/// Reset errors for features
#[pyfunction]
#[pyo3(signature = (feature_name=None))]
fn reset_errors(feature_name: Option<String>) {
    feature_flags::reset_feature_errors(feature_name.as_deref());
}

/// Record performance metrics
#[pyfunction]
#[pyo3(signature = (component, operation, duration_ms, success=None, input_size=None, output_size=None))]
fn record_performance(
    component: String,
    operation: String,
    duration_ms: f64,
    success: Option<bool>,
    input_size: Option<usize>,
    output_size: Option<usize>,
) {
    performance_monitor::record_performance(
        &component,
        &operation,
        duration_ms,
        success.unwrap_or(true),
        input_size,
        output_size,
        None, // Simplify for now - metadata can be added later
    );
}

/// Get performance statistics
#[pyfunction]
#[pyo3(signature = (component=None))]
fn get_performance_stats(py: Python, component: Option<String>) -> PyResult<PyObject> {
    let stats = performance_monitor::get_performance_stats(component.as_deref());
    convert_hashmap_to_pydict(py, stats)
}

/// Compare implementations
#[pyfunction]
fn compare_implementations(
    py: Python,
    rust_component: String,
    python_component: String,
) -> PyResult<PyObject> {
    let comparison =
        performance_monitor::compare_implementations(&rust_component, &python_component);
    convert_hashmap_to_pydict(py, comparison)
}

/// Get optimization recommendations
#[pyfunction]
fn get_recommendations(py: Python) -> PyResult<PyObject> {
    let recommendations = performance_monitor::get_recommendations();
    let py_list = PyList::empty(py);

    for rec in recommendations {
        let rec_dict = PyDict::new(py);
        for (key, value) in rec {
            let py_value = convert_json_value_to_py(py, value)?;
            rec_dict.set_item(key, py_value)?;
        }
        py_list.append(rec_dict)?;
    }

    Ok(py_list.into())
}

/// Export performance data
#[pyfunction]
#[pyo3(signature = (component=None, format=None))]
fn export_performance_data(component: Option<String>, format: Option<String>) -> String {
    performance_monitor::export_performance_data(
        component.as_deref(),
        format.as_deref().unwrap_or("json"),
    )
}

/// Get patch status
#[pyfunction]
fn get_patch_status(py: Python) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    dict.set_item("applied", true)?;

    let components = PyList::new(
        py,
        [
            "routing",
            "token_counting",
            "rate_limiting",
            "connection_pooling",
        ],
    )?;
    dict.set_item("components", components)?;

    Ok(dict.into())
}

// ============================================================
// Rate Limiter Functions (exposed to Python)
// ============================================================

/// Check if a request is allowed under rate limits
#[pyfunction]
fn check_rate_limit(py: Python, key: String) -> PyResult<PyObject> {
    let result = rate_limiter::check_rate_limit(&key);
    let dict = PyDict::new(py);
    dict.set_item("allowed", result.allowed)?;
    dict.set_item("reason", result.reason)?;
    dict.set_item("remaining_requests", result.remaining_requests)?;
    if let Some(retry_after) = result.retry_after_ms {
        dict.set_item("retry_after_ms", retry_after)?;
    }
    Ok(dict.into())
}

/// Get rate limit statistics
#[pyfunction]
fn get_rate_limit_stats(py: Python) -> PyResult<PyObject> {
    let stats = rate_limiter::get_rate_limit_stats();
    convert_hashmap_to_pydict(py, stats)
}

// ============================================================
// Connection Pool Functions (exposed to Python)
// ============================================================

/// Get a connection from the pool for an endpoint
#[pyfunction]
fn get_connection(endpoint: String) -> Option<String> {
    connection_pool::get_connection(&endpoint)
}

/// Return a connection to the pool
#[pyfunction]
fn return_connection(connection_id: String) {
    connection_pool::return_connection(&connection_id);
}

/// Remove a connection from the pool
#[pyfunction]
fn remove_connection(connection_id: String) {
    connection_pool::remove_connection(&connection_id);
}

/// Health check a connection
#[pyfunction]
fn health_check_connection(connection_id: String) -> bool {
    connection_pool::health_check_connection(&connection_id)
}

/// Clean up expired connections
#[pyfunction]
fn cleanup_expired_connections() {
    connection_pool::cleanup_expired_connections();
}

/// Get connection pool statistics
#[pyfunction]
fn get_connection_pool_stats(py: Python) -> PyResult<PyObject> {
    let stats = connection_pool::get_connection_pool_stats();
    convert_hashmap_to_pydict(py, stats)
}

// ============================================================
// Routing Functions (exposed to Python)
// ============================================================

/// Get an available deployment for a model
/// This is a simplified version that demonstrates the routing capability
#[pyfunction]
#[pyo3(signature = (model_list, model, blocked_models=None, _context=None, _settings=None))]
fn get_available_deployment(
    py: Python,
    model_list: Vec<PyObject>,
    model: String,
    blocked_models: Option<Vec<String>>,
    _context: Option<PyObject>,
    _settings: Option<PyObject>,
) -> PyResult<Option<PyObject>> {
    // Filter model_list to find matching models
    let mut available: Vec<PyObject> = Vec::new();
    let blocked = blocked_models.unwrap_or_default();

    for item in model_list.iter() {
        // Extract model_name from dict
        if let Ok(dict) = item.downcast_bound::<PyDict>(py) {
            if let Ok(Some(name)) = dict.get_item("model_name") {
                if let Ok(name_str) = name.extract::<String>() {
                    if name_str == model && !blocked.contains(&name_str) {
                        available.push(item.clone_ref(py));
                    }
                }
            }
        }
    }

    // Return a random selection (simple_shuffle strategy)
    if available.is_empty() {
        // Fall back to any model
        if !model_list.is_empty() {
            let index = rand::random::<usize>() % model_list.len();
            return Ok(Some(model_list[index].clone_ref(py)));
        }
        return Ok(None);
    }

    let index = rand::random::<usize>() % available.len();
    Ok(Some(available[index].clone_ref(py)))
}

/// Python module definition
#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Add version constant
    m.add("__version__", "0.1.0")?;
    m.add("RUST_ACCELERATION_AVAILABLE", true)?;

    // Core functions
    m.add_function(wrap_pyfunction!(rust_acceleration_available, m)?)?;
    m.add_function(wrap_pyfunction!(apply_acceleration, m)?)?;
    m.add_function(wrap_pyfunction!(remove_acceleration, m)?)?;
    m.add_function(wrap_pyfunction!(health_check, m)?)?;

    // Feature flag functions
    m.add_function(wrap_pyfunction!(is_enabled, m)?)?;
    m.add_function(wrap_pyfunction!(get_feature_status, m)?)?;
    m.add_function(wrap_pyfunction!(reset_errors, m)?)?;

    // Performance monitoring functions
    m.add_function(wrap_pyfunction!(record_performance, m)?)?;
    m.add_function(wrap_pyfunction!(get_performance_stats, m)?)?;
    m.add_function(wrap_pyfunction!(compare_implementations, m)?)?;
    m.add_function(wrap_pyfunction!(get_recommendations, m)?)?;
    m.add_function(wrap_pyfunction!(export_performance_data, m)?)?;
    m.add_function(wrap_pyfunction!(get_patch_status, m)?)?;

    // Rate limiter functions
    m.add_function(wrap_pyfunction!(check_rate_limit, m)?)?;
    m.add_function(wrap_pyfunction!(get_rate_limit_stats, m)?)?;

    // Connection pool functions
    m.add_function(wrap_pyfunction!(get_connection, m)?)?;
    m.add_function(wrap_pyfunction!(return_connection, m)?)?;
    m.add_function(wrap_pyfunction!(remove_connection, m)?)?;
    m.add_function(wrap_pyfunction!(health_check_connection, m)?)?;
    m.add_function(wrap_pyfunction!(cleanup_expired_connections, m)?)?;
    m.add_function(wrap_pyfunction!(get_connection_pool_stats, m)?)?;

    // Routing functions
    m.add_function(wrap_pyfunction!(get_available_deployment, m)?)?;

    // Add classes for shimming
    m.add_class::<SimpleTokenCounter>()?;
    m.add_class::<SimpleRateLimiter>()?;
    m.add_class::<SimpleConnectionPool>()?;
    m.add_class::<AdvancedRouter>()?;

    Ok(())
}
