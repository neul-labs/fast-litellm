//! Advanced router implementation for LiteLLM
//!
//! This module implements high-performance routing strategies that can be used
//! as drop-in replacements for the Python implementations.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, RwLock};
use std::time::Duration;
use thiserror::Error;
use tracing::{debug, info};

/// Core error types for the advanced router
#[derive(Error, Debug)]
pub enum RouterError {
    #[error("No healthy deployments available")]
    NoHealthyDeployments,
    #[error("Deployment not found: {0}")]
    DeploymentNotFound(String),
    #[error("Routing strategy error: {0}")]
    StrategyError(String),
    #[error("Cooldown period active for deployment: {0}")]
    CooldownActive(String),
    #[error("Health check failed: {0}")]
    HealthCheckFailed(String),
    #[error("PyO3 error: {0}")]
    PyO3Error(#[from] PyErr),
    #[error("Lock acquisition error: {0}")]
    LockError(String),
    #[error("Invalid deployment data: {0}")]
    InvalidDeploymentData(String),
    #[error("Routing failed: {0}")]
    RoutingFailed(String),
}

/// Routing strategies supported by the advanced router
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[pyclass]
pub enum RoutingStrategy {
    SimpleShuffle = 0,
    LeastBusy = 1,
    LatencyBased = 2,
    CostBased = 3,
    UsageBasedV1 = 4,
    UsageBasedV2 = 5,
    LeastBusyWithPenalty = 6,
}

#[pymethods]
impl RoutingStrategy {
    #[new]
    fn new(strategy_value: &PyAny) -> PyResult<Self> {
        // Handle both string values from Python and integer values
        if let Ok(strategy_str) = strategy_value.extract::<&str>() {
            match strategy_str {
                "simple-shuffle" => Ok(Self::SimpleShuffle),
                "least-busy" => Ok(Self::LeastBusy),
                "latency-based-routing" => Ok(Self::LatencyBased),
                "cost-based-routing" => Ok(Self::CostBased),
                "usage-based-routing" => Ok(Self::UsageBasedV1),
                "usage-based-routing-v2" => Ok(Self::UsageBasedV2),
                _ => Ok(Self::LeastBusy), // Default fallback
            }
        } else if let Ok(strategy_int) = strategy_value.extract::<i32>() {
            // Handle integer values as before
            match strategy_int {
                0 => Ok(Self::SimpleShuffle),
                1 => Ok(Self::LeastBusy),
                2 => Ok(Self::LatencyBased),
                3 => Ok(Self::CostBased),
                4 => Ok(Self::UsageBasedV1),
                5 => Ok(Self::UsageBasedV2),
                6 => Ok(Self::LeastBusyWithPenalty),
                _ => Ok(Self::LeastBusy),
            }
        } else {
            Ok(Self::LeastBusy) // Default fallback
        }
    }
    
    #[getter]
    fn strategy_id(&self) -> i32 {
        match self {
            Self::SimpleShuffle => 0,
            Self::LeastBusy => 1,
            Self::LatencyBased => 2,
            Self::CostBased => 3,
            Self::UsageBasedV1 => 4,
            Self::UsageBasedV2 => 5,
            Self::LeastBusyWithPenalty => 6,
        }
    }
    
    fn __str__(&self) -> &'static str {
        match self {
            Self::SimpleShuffle => "simple-shuffle",
            Self::LeastBusy => "least-busy",
            Self::LatencyBased => "latency-based-routing",
            Self::CostBased => "cost-based-routing",
            Self::UsageBasedV1 => "usage-based-routing",
            Self::UsageBasedV2 => "usage-based-routing-v2",
            Self::LeastBusyWithPenalty => "least-busy-with-penalty",
        }
    }
}

/// Represents a model deployment
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
    // Simple stats for PyO3 compatibility
    #[pyo3(get, set)]
    pub total_requests: u64,
    #[pyo3(get, set)]
    pub successful_requests: u64,
    #[pyo3(get, set)]
    pub failed_requests: u64,
    #[pyo3(get, set)]
    pub avg_latency_ms: f64,
    #[pyo3(get, set)]
    pub current_rpm: u64,
    #[pyo3(get, set)]
    pub current_tpm: u64,
    #[pyo3(get, set)]
    pub last_updated_timestamp: u64,
    // Cooldown timestamp (seconds since Unix epoch, 0 = no cooldown)
    #[pyo3(get, set)]
    pub cooldown_until_timestamp: u64,
    #[pyo3(get, set)]
    pub is_healthy: bool,
    // Last health check timestamp (seconds since Unix epoch)
    #[pyo3(get, set)]
    pub last_health_check_timestamp: u64,
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
            total_requests: 0,
            successful_requests: 0,
            failed_requests: 0,
            avg_latency_ms: 0.0,
            current_rpm: 0,
            current_tpm: 0,
            last_updated_timestamp: 0,
            cooldown_until_timestamp: 0, // No cooldown initially
            is_healthy: true,
            last_health_check_timestamp: 0,
        })
    }
    
    /// Check if deployment is currently in cooldown
    fn is_in_cooldown(&self) -> bool {
        if self.cooldown_until_timestamp > 0 {
            let current_timestamp = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or(std::time::Duration::from_secs(0))
                .as_secs();
            current_timestamp < self.cooldown_until_timestamp
        } else {
            false
        }
    }
    
    #[getter]
    fn get_total_requests(&self) -> u64 {
        self.total_requests
    }
    
    #[getter]
    fn get_successful_requests(&self) -> u64 {
        self.successful_requests
    }
    
    #[getter]
    fn get_failed_requests(&self) -> u64 {
        self.failed_requests
    }
    
    #[getter]
    fn get_avg_latency(&self) -> f64 {
        self.avg_latency_ms
    }
    
    #[getter]
    fn get_current_rpm(&self) -> u64 {
        self.current_rpm
    }
    
    #[getter]
    fn get_current_tpm(&self) -> u64 {
        self.current_tpm
    }
    
    #[getter]
    fn get_last_updated(&self) -> u64 {
        self.last_updated_timestamp
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

/// Router configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct RouterConfig {
    #[pyo3(get, set)]
    pub routing_strategy: RoutingStrategy,
    #[pyo3(get, set)]
    pub cooldown_time_seconds: u64,
    #[pyo3(get, set)]
    pub max_retries: usize,
    #[pyo3(get, set)]
    pub timeout_seconds: u64,
}

/// Advanced router implementation
#[derive(Debug, Clone)]
#[pyclass]
pub struct AdvancedRouter {
    deployments: Arc<RwLock<HashMap<String, Deployment>>>,
    config: RouterConfig,
    request_counter: Arc<AtomicU64>,
}

#[pymethods]
impl RouterConfig {
    #[new]
    fn new(
        routing_strategy: RoutingStrategy,
        cooldown_time_seconds: u64,
        max_retries: usize,
        timeout_seconds: u64,
    ) -> Self {
        Self {
            routing_strategy,
            cooldown_time_seconds,
            max_retries,
            timeout_seconds,
        }
    }
}

impl AdvancedRouter {
    /// Get deployment attribute as f64 without copying
    fn get_deployment_attr_f64(&self, py: Python, deployment: &PyObject, attr_name: &str) -> PyResult<f64> {
        let deployment_bound = deployment.as_ref(py);
        let attr = deployment_bound.getattr(attr_name)?;
        attr.extract()
    }
    
    /// Get deployment attribute as u64 without copying
    fn get_deployment_attr_u64(&self, py: Python, deployment: &PyObject, attr_name: &str) -> PyResult<u64> {
        let deployment_bound = deployment.as_ref(py);
        let attr = deployment_bound.getattr(attr_name)?;
        attr.extract()
    }
}

#[pymethods]
impl AdvancedRouter {
    /// Create a new AdvancedRouter instance (original constructor)
    #[new]
    fn new(config: RouterConfig) -> PyResult<Self> {
        Ok(Self {
            deployments: Arc::new(RwLock::new(HashMap::new())),
            config,
            request_counter: Arc::new(AtomicU64::new(0)),
        })
    }

    /// Check if Rust acceleration is available
    fn is_available(&self) -> bool {
        true
    }

    /// Add a deployment to the router
    fn add_deployment(&mut self, deployment: Deployment) -> PyResult<()> {
        debug!("Adding deployment: {}", deployment.model_name);
        let mut deployments = self.deployments.write()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire write lock".to_string()
            ))?;
        deployments.insert(deployment.model_name.clone(), deployment);
        Ok(())
    }

    /// Remove a deployment from the router
    fn remove_deployment(&mut self, deployment_id: &str) -> PyResult<bool> {
        debug!("Removing deployment: {}", deployment_id);
        let mut deployments = self.deployments.write()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire write lock".to_string()
            ))?;
        let removed = deployments.remove(deployment_id).is_some();
        Ok(removed)
    }

    /// Get all deployment names
    fn get_deployment_names(&self) -> PyResult<Vec<String>> {
        let deployments = self.deployments.read()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire read lock".to_string()
            ))?;
        Ok(deployments.keys().cloned().collect())
    }

    /// Get deployment by ID
    fn get_deployment(&self, deployment_id: &str) -> PyResult<Option<Deployment>> {
        let deployments = self.deployments.read()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire read lock".to_string()
            ))?;
        Ok(deployments.get(deployment_id).cloned())
    }

    /// Route a request to an appropriate deployment
    #[pyo3(signature = (model_name, request_data))]
    fn route_request(&self, py: Python, model_name: &str, request_data: &PyAny) -> PyResult<PyObject> {
        debug!("Routing request for model: {}", model_name);
        
        // Increment request counter
        self.request_counter.fetch_add(1, Ordering::Relaxed);
        
        // Get healthy deployments for this model
        let healthy_deployments = self.get_healthy_deployments(py, model_name)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                format!("Failed to get healthy deployments for model {}: {}", model_name, e)
            ))?;
        
        if healthy_deployments.is_empty() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("No healthy deployments found for model: {}", model_name)
            ));
        }
        
        // Select deployment based on routing strategy
        let deployments_list = PyList::new(py, healthy_deployments);
        let selected_deployment = match self.config.routing_strategy {
            RoutingStrategy::SimpleShuffle => self.simple_shuffle(py, deployments_list)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Simple shuffle routing failed: {}", e)
                ))?,
            RoutingStrategy::LeastBusy => self.least_busy(py, deployments_list)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Least busy routing failed: {}", e)
                ))?,
            RoutingStrategy::LatencyBased => self.latency_based(py, deployments_list)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Latency-based routing failed: {}", e)
                ))?,
            RoutingStrategy::CostBased => self.cost_based(py, deployments_list)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Cost-based routing failed: {}", e)
                ))?,
            RoutingStrategy::UsageBasedV1 => self.usage_based_v1(py, deployments_list)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Usage-based v1 routing failed: {}", e)
                ))?,
            RoutingStrategy::UsageBasedV2 => self.usage_based_v2(py, deployments_list)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Usage-based v2 routing failed: {}", e)
                ))?,
            RoutingStrategy::LeastBusyWithPenalty => self.least_busy_with_penalty(py, deployments_list)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Least busy with penalty routing failed: {}", e)
                ))?,
        };
        
        Ok(selected_deployment)
    }

    /// Get healthy deployments for a model
    fn get_healthy_deployments(&self, py: Python, model_name: &str) -> PyResult<Vec<PyObject>> {
        let deployments = self.deployments.read()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire read lock".to_string()
            ))?;
        let mut healthy_deployments = Vec::new();
        
        for (_, deployment) in deployments.iter() {
            if deployment.model_name == model_name 
                && deployment.is_healthy
                && !deployment.is_in_cooldown() {
                healthy_deployments.push(deployment.clone().into_py(py));
            }
        }
        
        Ok(healthy_deployments)
    }

    /// Simple shuffle routing strategy
    fn simple_shuffle(&self, py: Python, deployments: &PyList) -> PyResult<PyObject> {
        if deployments.len() == 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "No deployments available for routing".to_string()
            ));
        }
        
        // Simple random selection for now
        use rand::seq::SliceRandom;
        let mut rng = rand::thread_rng();
        
        // Convert PyList to Vec for random selection
        let deployment_vec: Vec<PyObject> = (0..deployments.len())
            .map(|i| deployments.get_item(i).unwrap().into())
            .collect();
            
        let selected = deployment_vec
            .choose(&mut rng)
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Failed to select deployment".to_string()
            ))?;
        
        Ok(selected.clone())
    }

    /// Least busy routing strategy
    fn least_busy(&self, _py: Python, deployments: &PyList) -> PyResult<PyObject> {
        if deployments.len() == 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "No deployments available for routing".to_string()
            ));
        }
        
        // Find deployment with lowest current RPM
        let mut min_rpm = u64::MAX;
        let mut selected_deployment: Option<PyObject> = None;
        
        for i in 0..deployments.len() {
            let deployment_obj = deployments.get_item(i)?;
            let rpm_attr = deployment_obj.getattr("current_rpm")?;
            let rpm: u64 = rpm_attr.extract()?;
            
            if rpm < min_rpm {
                min_rpm = rpm;
                selected_deployment = Some(deployment_obj.into());
            }
        }
        
        if let Some(deployment) = selected_deployment {
            Ok(deployment)
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Failed to select deployment with least busy strategy".to_string()
            ))
        }
    }

    /// Latency-based routing strategy
    fn latency_based(&self, _py: Python, deployments: &PyList) -> PyResult<PyObject> {
        if deployments.len() == 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "No deployments available for routing".to_string()
            ));
        }
        
        // Find deployment with lowest average latency
        let mut min_latency = f64::INFINITY;
        let mut selected_deployment: Option<PyObject> = None;
        
        for i in 0..deployments.len() {
            let deployment_obj = deployments.get_item(i)?;
            let latency_attr = deployment_obj.getattr("avg_latency_ms")?;
            let latency: f64 = latency_attr.extract()?;
            
            if latency < min_latency {
                min_latency = latency;
                selected_deployment = Some(deployment_obj.into());
            }
        }
        
        if let Some(deployment) = selected_deployment {
            Ok(deployment)
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Failed to select deployment with latency-based strategy".to_string()
            ))
        }
    }

    /// Cost-based routing strategy
    fn cost_based(&self, _py: Python, deployments: &PyList) -> PyResult<PyObject> {
        if deployments.len() == 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "No deployments available for routing".to_string()
            ));
        }
        
        // Parse model info to get costs
        let mut lowest_cost = f64::INFINITY;
        let mut selected_deployment: Option<PyObject> = None;
        
        for i in 0..deployments.len() {
            let deployment_py = deployments.get_item(i)?;
            // Access model_info attribute directly without copying
            let model_info_attr = deployment_py.getattr("model_info")?;
            
            // Extract cost information directly from Python objects
            let input_cost = model_info_attr.getattr("input_cost_per_token")
                .ok()
                .and_then(|item| item.extract().ok())
                .unwrap_or(0.0);
            let output_cost = model_info_attr.getattr("output_cost_per_token")
                .ok()
                .and_then(|item| item.extract().ok())
                .unwrap_or(0.0);
            let total_cost = input_cost + output_cost;
            
            if total_cost < lowest_cost {
                lowest_cost = total_cost;
                selected_deployment = Some(deployment_py.into());
            }
        }
        
        if let Some(deployment) = selected_deployment {
            Ok(deployment)
        } else {
            // Fallback to first deployment if no cost found
            let first_deployment = deployments.get_item(0)?;
            Ok(first_deployment.into())
        }
    }

    /// Usage-based routing strategy v1
    fn usage_based_v1(&self, _py: Python, deployments: &PyList) -> PyResult<PyObject> {
        if deployments.len() == 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "No deployments available for routing".to_string()
            ));
        }
        
        // Find deployment with lowest combined usage (RPM + TPM)
        let mut min_usage = u64::MAX;
        let mut selected_deployment: Option<PyObject> = None;
        
        for i in 0..deployments.len() {
            let deployment_obj = deployments.get_item(i)?;
            let rpm_attr = deployment_obj.getattr("current_rpm")?;
            let tpm_attr = deployment_obj.getattr("current_tpm")?;
            let rpm: u64 = rpm_attr.extract()?;
            let tpm: u64 = tpm_attr.extract()?;
            let usage = rpm + tpm;
            
            if usage < min_usage {
                min_usage = usage;
                selected_deployment = Some(deployment_obj.into());
            }
        }
        
        if let Some(deployment) = selected_deployment {
            Ok(deployment)
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Failed to select deployment with usage-based strategy v1".to_string()
            ))
        }
    }

    /// Usage-based routing strategy v2
    fn usage_based_v2(&self, _py: Python, deployments: &PyList) -> PyResult<PyObject> {
        if deployments.len() == 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "No deployments available for routing".to_string()
            ));
        }
        
        // Find deployment with lowest percentage of usage limits
        let mut min_usage = f64::INFINITY;
        let mut selected_deployment: Option<PyObject> = None;
        
        for i in 0..deployments.len() {
            let deployment_obj = deployments.get_item(i)?;
            let rpm_attr = deployment_obj.getattr("current_rpm")?;
            let tpm_attr = deployment_obj.getattr("current_tpm")?;
            let rpm: u64 = rpm_attr.extract()?;
            let tpm: u64 = tpm_attr.extract()?;
            
            // Calculate usage percentages (placeholder values)
            let rpm_pct = rpm as f64 / 1000.0; // Placeholder limit
            let tpm_pct = tpm as f64 / 100000.0; // Placeholder limit
            let usage = rpm_pct + tpm_pct;
            
            if usage < min_usage {
                min_usage = usage;
                selected_deployment = Some(deployment_obj.into());
            }
        }
        
        if let Some(deployment) = selected_deployment {
            Ok(deployment)
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Failed to select deployment with usage-based strategy v2".to_string()
            ))
        }
    }

    /// Least busy with penalty routing strategy
    fn least_busy_with_penalty(&self, _py: Python, deployments: &PyList) -> PyResult<PyObject> {
        if deployments.len() == 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "No deployments available for routing".to_string()
            ));
        }
        
        // Find deployment with lowest current RPM, with penalty for high latency
        let mut min_score = f64::INFINITY;
        let mut selected_deployment: Option<PyObject> = None;
        
        for i in 0..deployments.len() {
            let deployment_obj = deployments.get_item(i)?;
            let rpm_attr = deployment_obj.getattr("current_rpm")?;
            let latency_attr = deployment_obj.getattr("avg_latency_ms")?;
            let rpm: u64 = rpm_attr.extract()?;
            let latency: f64 = latency_attr.extract()?;
            
            let score = rpm as f64 + (latency / 100.0); // Penalty factor
            
            if score < min_score {
                min_score = score;
                selected_deployment = Some(deployment_obj.into());
            }
        }
        
        if let Some(deployment) = selected_deployment {
            Ok(deployment)
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Failed to select deployment with least busy with penalty strategy".to_string()
            ))
        }
    }

    /// Update deployment statistics after a successful request
    fn update_deployment_stats(&mut self, deployment_id: &str, latency_ms: f64, tokens: u32) -> PyResult<()> {
        let mut deployments = self.deployments.write()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire write lock".to_string()
            ))?;
        if let Some(deployment) = deployments.get_mut(deployment_id) {
            // Update average latency using exponential moving average
            if deployment.avg_latency_ms == 0.0 {
                deployment.avg_latency_ms = latency_ms;
            } else {
                deployment.avg_latency_ms = 0.9 * deployment.avg_latency_ms + 0.1 * latency_ms;
            }
            
            // Update token counts
            deployment.current_tpm += tokens as u64;
            deployment.total_requests += 1;
            deployment.successful_requests += 1;
            deployment.failed_requests += 0; // No failures
            deployment.current_rpm += 1; // Simplified for now
            
            // Update last updated time
            deployment.last_updated_timestamp = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or(std::time::Duration::from_secs(0))
                .as_secs();
        }
        Ok(())
    }

    /// Mark deployment as unhealthy
    fn mark_deployment_unhealthy(&mut self, deployment_id: &str) -> PyResult<()> {
        let mut deployments = self.deployments.write()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire write lock".to_string()
            ))?;
        if let Some(deployment) = deployments.get_mut(deployment_id) {
            deployment.is_healthy = false;
            let cooldown_duration = Duration::from_secs(self.config.cooldown_time_seconds);
            deployment.cooldown_until_timestamp = (std::time::SystemTime::now() + cooldown_duration)
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or(std::time::Duration::from_secs(0))
                .as_secs();
            deployment.failed_requests += 1;
            deployment.total_requests += 1;
            deployment.last_updated_timestamp = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or(std::time::Duration::from_secs(0))
                .as_secs();
        }
        Ok(())
    }

    /// Get router statistics
    #[pyo3(signature = ())]
    fn get_stats(&self, py: Python) -> PyResult<PyObject> {
        let stats_dict = PyDict::new(py);
        
        // Convert atomic values to Python objects directly
        let total_requests = self.request_counter.load(Ordering::Relaxed);
        stats_dict.set_item("total_requests", total_requests)?;
        
        let deployments = self.deployments.read()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Failed to acquire read lock".to_string()
            ))?;
        
        let total_deployments = deployments.len();
        stats_dict.set_item("total_deployments", total_deployments)?;
        
        let healthy_count = deployments.values().filter(|d| d.is_healthy && !d.is_in_cooldown()).count();
        stats_dict.set_item("healthy_deployments", healthy_count)?;
        
        Ok(stats_dict.into())
    }
    
    /// Add completion method for API compatibility
    fn completion(&self, _py: Python, _model: &str, _messages: &PyList, _kwargs: Option<&PyDict>) -> PyResult<PyObject> {
        // This is a placeholder implementation - in a real implementation,
        // this would route the request and call the actual LLM API
        Ok(_py.None().into())
    }
    
    /// Add acompletion method for API compatibility
    fn acompletion(&self, _py: Python, _model: &str, _messages: &PyList, _stream: bool, _kwargs: Option<&PyDict>) -> PyResult<PyObject> {
        // This is a placeholder implementation - in a real implementation,
        // this would route the request and call the actual async LLM API
        Ok(_py.None().into())
    }
}

/// Health check function for advanced router components
#[pyfunction]
pub fn advanced_router_health_check() -> PyResult<bool> {
    info!("Advanced router health check called");
    Ok(true)
}