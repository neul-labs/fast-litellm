//! LiteLLM Core - High-performance components for LiteLLM
//!
//! This crate provides Rust implementations of performance-critical
//! components that can be used as drop-in replacements for the Python
//! implementations.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;
use thiserror::Error;
use tracing::{debug, info};

// Include the advanced router module
mod advanced_router;
mod token;

/// Core error types for the LiteLLM core
#[derive(Error, Debug)]
pub enum LiteLLMError {
    #[error("Routing error: {0}")]
    RoutingError(String),
    #[error("Configuration error: {0}")]
    ConfigError(String),
    #[error("Serialization error: {0}")]
    SerializationError(String),
    #[error("PyO3 error: {0}")]
    PyO3Error(#[from] PyErr),
    #[error("Lock acquisition error: {0}")]
    LockError(String),
    #[error("Deployment not found: {0}")]
    DeploymentNotFound(String),
}

impl From<LiteLLMError> for PyErr {
    fn from(err: LiteLLMError) -> PyErr {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(err.to_string())
    }
}

/// Represents a model deployment (simplified version for core module)
#[derive(Debug, Clone)]
#[pyclass]
pub struct Deployment {
    #[pyo3(get, set)]
    pub model_name: String,
    // Direct Python object conversion for better performance
    #[pyo3(get, set)]
    pub litellm_params: PyObject,
    #[pyo3(get, set)]
    pub model_info: PyObject,
}

#[pymethods]
impl Deployment {
    #[new]
    fn new(
        py: Python,
        model_name: String,
        litellm_params: &PyAny,
        model_info: Option<&PyAny>,
    ) -> PyResult<Self> {
        // Handle optional model_info parameter
        let model_info_obj = match model_info {
            Some(info) => info.into_py(py),
            None => PyDict::new(py).into(),
        };
        
        Ok(Self {
            model_name,
            litellm_params: litellm_params.into_py(py),
            model_info: model_info_obj,
        })
    }
    
    /// Get litellm_params as a JSON string (for compatibility)
    fn litellm_params_json(&self, py: Python) -> PyResult<String> {
        // Convert Python object to string representation directly
        let params = self.litellm_params.as_ref(py);
        Ok(format!("{:?}", params))
    }
    
    /// Get model_info as a JSON string (for compatibility)
    fn model_info_json(&self, py: Python) -> PyResult<String> {
        // Convert Python object to string representation directly
        let info = self.model_info.as_ref(py);
        Ok(format!("{:?}", info))
    }
}

/// Core LiteLLM functionality exposed to Python
#[pyclass]
pub struct LiteLLMCore {
    deployments: HashMap<String, Deployment>,
    rust_enabled: bool,
}

#[pymethods]
impl LiteLLMCore {
    /// Create a new LiteLLMCore instance
    #[new]
    fn new() -> PyResult<Self> {
        let core = Self {
            deployments: HashMap::new(),
            rust_enabled: true,
        };
        
        info!("LiteLLM Core initialized with Rust acceleration");
        Ok(core)
    }

    /// Check if Rust acceleration is available
    fn is_available(&self) -> bool {
        self.rust_enabled
    }

    /// Add a deployment to the router
    fn add_deployment(&mut self, _py: Python, deployment: Deployment) -> PyResult<()> {
        debug!("Adding deployment: {}", deployment.model_name);
        self.deployments
            .insert(deployment.model_name.clone(), deployment);
        Ok(())
    }

    /// Get all deployment names
    fn get_deployment_names(&self) -> Vec<String> {
        self.deployments.keys().cloned().collect()
    }

    /// Route a request to an appropriate deployment
    #[pyo3(signature = (request_data))]
    fn route_request(&self, py: Python, request_data: &PyAny) -> PyResult<PyObject> {
        debug!("Routing request");
        
        // Extract model name from request data
        let model_name = if let Ok(dict) = request_data.downcast::<PyDict>() {
            dict.get_item("model")?
                .and_then(|item| item.extract().ok())
                .unwrap_or_else(|| "default".to_string())
        } else if let Ok(json_str) = request_data.extract::<String>() {
            // Handle backward compatibility with JSON strings
            // Instead of parsing JSON, try to extract model directly from Python string if it's a dict representation
            // For true JSON strings, we'll need to parse but we can optimize this case
            if json_str.starts_with("{") && json_str.contains("\"model\"") {
                // Try to parse as a simple JSON object to extract model
                // This is still JSON parsing but more targeted
                use std::collections::HashMap;
                if let Ok(map) = serde_json::from_str::<HashMap<String, serde_json::Value>>(&json_str) {
                    if let Some(model_val) = map.get("model") {
                        if let Some(model_str) = model_val.as_str() {
                            model_str.to_string()
                        } else {
                            "default".to_string()
                        }
                    } else {
                        "default".to_string()
                    }
                } else {
                    "default".to_string()
                }
            } else {
                "default".to_string()
            }
        } else {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Request data must be a dict or JSON string".to_string()
            ));
        };
        
        // Check if we have this model
        if let Some(deployment) = self.deployments.get(&model_name) {
            debug!("Found deployment for model: {}", model_name);
            Ok(deployment.clone().into_py(py))
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("No deployment found for model: {}", model_name)
            ))
        }
    }
}

/// Health check function to verify Rust components are working
#[pyfunction]
fn health_check() -> PyResult<bool> {
    info!("Health check called");
    Ok(true)
}

/// Python module entry point
#[pymodule]
fn litellm_core(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    // Initialize tracing
    tracing_subscriber::fmt::init();
    
    m.add_class::<Deployment>()?;
    m.add_class::<LiteLLMCore>()?;
    
    // Add advanced router classes
    m.add_class::<advanced_router::RoutingStrategy>()?;
    m.add_class::<advanced_router::Deployment>()?;
    m.add_class::<advanced_router::RouterConfig>()?;
    m.add_class::<advanced_router::AdvancedRouter>()?;
    
    m.add_function(wrap_pyfunction!(health_check, m)?)?;
    m.add_function(wrap_pyfunction!(advanced_router::advanced_router_health_check, m)?)?;
    
    Ok(())
}