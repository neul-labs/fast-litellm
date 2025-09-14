//! Token counting and rate limiting implementation for LiteLLM
//!
//! High-performance token counting and rate limiting using Rust.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::{HashMap, VecDeque};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};
use thiserror::Error;
use tiktoken_rs::{get_bpe_from_model, CoreBPE};
use tracing::{debug, info};

/// Get BPE encoding for a model
fn get_bpe_for_model(model: &str) -> Result<CoreBPE, TokenError> {
    get_bpe_from_model(model)
        .map_err(|e| TokenError::ModelNotSupported(format!("{}: {}", model, e)))
}

/// Core error types for token counting and rate limiting
#[derive(Error, Debug)]
pub enum TokenError {
    #[error("Token counting error: {0}")]
    CountingError(String),
    #[error("Rate limiting error: {0}")]
    RateLimitError(String),
    #[error("Cache error: {0}")]
    CacheError(String),
    #[error("Model not supported: {0}")]
    ModelNotSupported(String),
}

/// Token counter implementation with tiktoken integration
#[derive(Clone)]
#[pyclass]
pub struct SimpleTokenCounter {
    /// Cache for model encodings
    encodings: Arc<RwLock<HashMap<String, CoreBPE>>>,
    /// Maximum cache size
    #[pyo3(get, set)]
    pub cache_size: usize,
}

#[pymethods]
impl SimpleTokenCounter {
    #[new]
    fn new(cache_size: usize) -> Self {
        Self {
            encodings: Arc::new(RwLock::new(HashMap::new())),
            cache_size,
        }
    }

    /// Count tokens in a text for a specific model
    #[pyo3(signature = (text, model))]
    fn count_tokens(&self, _py: Python, text: &str, model: &str) -> PyResult<usize> {
        debug!("Counting tokens for model: {}", model);
        
        // Try to get encoding from cache first
        {
            let encodings = self.encodings.read()
                .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    "Failed to acquire read lock".to_string()
                ))?;
            
            if let Some(bpe) = encodings.get(model) {
                let tokens = bpe.encode_with_special_tokens(text);
                return Ok(tokens.len());
            }
        }
        
        // Load encoding for model
        match get_bpe_for_model(model) {
            Ok(bpe) => {
                let token_count = bpe.encode_with_special_tokens(text).len();
                
                // Cache the encoding if we have space
                {
                    let mut encodings = self.encodings.write()
                        .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                            "Failed to acquire write lock".to_string()
                        ))?;
                    
                    if encodings.len() < self.cache_size {
                        encodings.insert(model.to_string(), bpe);
                    }
                }
                
                Ok(token_count)
            },
            Err(_) => {
                // Fallback to character-based counting if model not supported
                let char_count = text.chars().count();
                let approx_token_length = 4; // Average token length approximation
                let token_count = (char_count + approx_token_length - 1) / approx_token_length;
                Ok(token_count)
            }
        }
    }

    /// Count tokens in multiple texts for a specific model
    #[pyo3(signature = (texts, model))]
    fn count_tokens_batch(&self, py: Python, texts: &PyAny, model: &str) -> PyResult<PyObject> {
        debug!("Counting tokens for batch of texts");
        
        // Convert PyAny to Vec<String>
        let texts_vec: Vec<String> = if let Ok(text_list) = texts.downcast::<pyo3::types::PyList>() {
            text_list.iter()
                .map(|item| item.extract::<String>())
                .collect::<Result<Vec<String>, _>>()?
        } else {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Expected a list of texts".to_string()
            ));
        };
        
        let result_list = pyo3::types::PyList::empty(py);
        
        for text in texts_vec {
            let token_count = self.count_tokens(py, &text, model)?;
            result_list.append(token_count)?;
        }
        
        Ok(result_list.into())
    }

    /// Get cache statistics
    #[pyo3(signature = ())]
    fn get_cache_stats(&self, py: Python) -> PyResult<PyObject> {
        let encodings = self.encodings.read()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire read lock".to_string()
            ))?;
        
        let stats_dict = PyDict::new(py);
        stats_dict.set_item("cached_encodings", encodings.len())?;
        stats_dict.set_item("max_cache_size", self.cache_size)?;
        
        Ok(stats_dict.into())
    }
}

/// Rate limiting implementation with sliding windows
#[derive(Clone)]
#[pyclass]
pub struct SimpleRateLimiter {
    /// Rate limit windows
    windows: Arc<RwLock<HashMap<String, SlidingWindow>>>,
}

#[derive(Debug)]
struct SlidingWindow {
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

/// Health check function for token counting components
#[pyfunction]
pub fn token_health_check() -> PyResult<bool> {
    info!("Token counting health check called");
    Ok(true)
}

/// Python module entry point for token counting
#[pymodule]
fn litellm_token(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    // Initialize tracing
    tracing_subscriber::fmt::init();
    
    m.add_class::<SimpleTokenCounter>()?;
    m.add_class::<SimpleRateLimiter>()?;
    
    m.add_function(wrap_pyfunction!(token_health_check, m)?)?;
    
    Ok(())
}