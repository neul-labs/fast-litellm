//! Rate limiting implementation for LiteLLM
//!
//! High-performance rate limiting using Rust.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::{HashMap, VecDeque};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};
use thiserror::Error;
use tracing::{debug, info};

/// Core error types for rate limiting
#[derive(Error, Debug)]
pub enum RateLimitError {
    #[error("Rate limiting error: {0}")]
    LimitingError(String),
    #[error("Cache error: {0}")]
    CacheError(String),
    #[error("PyO3 error: {0}")]
    PyO3Error(#[from] PyErr),
    #[error("Lock acquisition error: {0}")]
    LockError(String),
}

impl From<RateLimitError> for PyErr {
    fn from(err: RateLimitError) -> PyErr {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(err.to_string())
    }
}

/// Simple rate limiter implementation
#[derive(Debug, Clone)]
#[pyclass]
pub struct SimpleRateLimiter {
    /// Rate limit windows
    windows: Arc<RwLock<HashMap<String, SlidingWindow>>>,
}

#[derive(Debug)]
struct SlidingWindow {
    start_time: Instant,
    requests: VecDeque<Instant>,
    token_count: AtomicU64,
}

#[pymethods]
impl SimpleRateLimiter {
    #[new]
    fn new() -> Self {
        Self {
            windows: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Check if a request is within rate limits
    #[pyo3(signature = (key, limit, window_seconds))]
    fn check_rate_limit(&self, key: &str, limit: u64, window_seconds: u64) -> PyResult<bool> {
        debug!("Checking rate limit for key: {}", key);
        
        let now = Instant::now();
        let window_duration = Duration::from_secs(window_seconds);
        
        let mut windows = self.windows.write()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire write lock".to_string()
            ))?;
        
        let window = windows.entry(key.to_string())
            .or_insert_with(|| SlidingWindow {
                start_time: now,
                requests: VecDeque::new(),
                token_count: AtomicU64::new(0),
            });
        
        // Remove expired requests
        let window_start = now - window_duration;
        while let Some(front) = window.requests.front() {
            if *front < window_start {
                window.requests.pop_front();
            } else {
                break;
            }
        }
        
        // Check if we're within limits
        let current_requests = window.requests.len() as u64;
        Ok(current_requests < limit)
    }

    /// Consume tokens from rate limit
    #[pyo3(signature = (key, tokens))]
    fn consume_tokens(&mut self, key: &str, tokens: u64) -> PyResult<bool> {
        debug!("Consuming {} tokens for key: {}", tokens, key);
        
        let now = Instant::now();
        
        let mut windows = self.windows.write()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire write lock".to_string()
            ))?;
        
        let window = windows.entry(key.to_string())
            .or_insert_with(|| SlidingWindow {
                start_time: now,
                requests: VecDeque::new(),
                token_count: AtomicU64::new(0),
            });
        
        window.requests.push_back(now);
        window.token_count.fetch_add(tokens, Ordering::Relaxed);
        
        Ok(true)
    }

    /// Get rate limit statistics
    #[pyo3(signature = ())]
    fn get_rate_limit_stats(&self, py: Python) -> PyResult<PyObject> {
        let windows = self.windows.read()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire read lock".to_string()
            ))?;
        
        let stats_dict = PyDict::new(py);
        stats_dict.set_item("tracked_keys", windows.len())?;
        
        let total_requests: usize = windows.values()
            .map(|w| w.requests.len())
            .sum();
        stats_dict.set_item("total_requests", total_requests)?;
        
        Ok(stats_dict.into())
    }
}

/// Health check function for rate limiting components
#[pyfunction]
pub fn rate_limit_health_check() -> PyResult<bool> {
    info!("Rate limiting health check called");
    Ok(true)
}

/// Python module entry point for rate limiting
#[pymodule]
fn litellm_rate_limiter(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    // Initialize tracing
    tracing_subscriber::fmt::init();
    
    m.add_class::<SimpleRateLimiter>()?;
    
    m.add_function(wrap_pyfunction!(rate_limit_health_check, m)?)?;
    
    Ok(())
}