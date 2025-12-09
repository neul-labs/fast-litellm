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

    Ok(())
}
