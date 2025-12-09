use dashmap::DashMap;
use serde::{Deserialize, Serialize};
/// Core routing and load balancing functionality
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RouteConfig {
    pub strategy: String,
    pub endpoints: Vec<String>,
    pub weights: Option<Vec<f64>>,
}

pub struct AdvancedRouter {
    routes: DashMap<String, RouteConfig>,
    metrics: DashMap<String, RouteMetrics>,
}

#[derive(Debug, Clone)]
struct RouteMetrics {
    latency_ms: f64,
    success_rate: f64,
    cost_per_request: f64,
    active_requests: u32,
}

impl Default for AdvancedRouter {
    fn default() -> Self {
        Self::new()
    }
}

impl AdvancedRouter {
    pub fn new() -> Self {
        Self {
            routes: DashMap::new(),
            metrics: DashMap::new(),
        }
    }

    pub fn add_route(&self, name: String, config: RouteConfig) {
        self.routes.insert(name, config);
    }

    pub fn select_endpoint(&self, route_name: &str) -> Option<String> {
        let route = self.routes.get(route_name)?;

        match route.strategy.as_str() {
            "simple_shuffle" => self.simple_shuffle_selection(&route),
            "least_busy" => self.least_busy_selection(&route),
            "latency_based" => self.latency_based_selection(&route),
            "cost_based" => self.cost_based_selection(&route),
            _ => self.simple_shuffle_selection(&route),
        }
    }

    fn simple_shuffle_selection(&self, route: &RouteConfig) -> Option<String> {
        if route.endpoints.is_empty() {
            return None;
        }

        let index = rand::random::<usize>() % route.endpoints.len();
        Some(route.endpoints[index].clone())
    }

    fn least_busy_selection(&self, route: &RouteConfig) -> Option<String> {
        let mut best_endpoint = None;
        let mut min_requests = u32::MAX;

        for endpoint in &route.endpoints {
            if let Some(metrics) = self.metrics.get(endpoint) {
                if metrics.active_requests < min_requests {
                    min_requests = metrics.active_requests;
                    best_endpoint = Some(endpoint.clone());
                }
            } else {
                // No metrics means unused endpoint, prefer it
                return Some(endpoint.clone());
            }
        }

        best_endpoint.or_else(|| route.endpoints.first().cloned())
    }

    fn latency_based_selection(&self, route: &RouteConfig) -> Option<String> {
        let mut best_endpoint = None;
        let mut min_latency = f64::MAX;

        for endpoint in &route.endpoints {
            if let Some(metrics) = self.metrics.get(endpoint) {
                if metrics.latency_ms < min_latency {
                    min_latency = metrics.latency_ms;
                    best_endpoint = Some(endpoint.clone());
                }
            }
        }

        best_endpoint.or_else(|| route.endpoints.first().cloned())
    }

    fn cost_based_selection(&self, route: &RouteConfig) -> Option<String> {
        let mut best_endpoint = None;
        let mut min_cost = f64::MAX;

        for endpoint in &route.endpoints {
            if let Some(metrics) = self.metrics.get(endpoint) {
                if metrics.cost_per_request < min_cost {
                    min_cost = metrics.cost_per_request;
                    best_endpoint = Some(endpoint.clone());
                }
            }
        }

        best_endpoint.or_else(|| route.endpoints.first().cloned())
    }

    pub fn update_metrics(&self, endpoint: &str, latency: f64, success: bool, cost: f64) {
        let mut metrics =
            self.metrics
                .entry(endpoint.to_string())
                .or_insert_with(|| RouteMetrics {
                    latency_ms: latency,
                    success_rate: if success { 1.0 } else { 0.0 },
                    cost_per_request: cost,
                    active_requests: 0,
                });

        // Simple exponential moving average
        metrics.latency_ms = 0.9 * metrics.latency_ms + 0.1 * latency;
        metrics.success_rate = 0.9 * metrics.success_rate + 0.1 * if success { 1.0 } else { 0.0 };
        metrics.cost_per_request = 0.9 * metrics.cost_per_request + 0.1 * cost;
    }

    pub fn increment_active_requests(&self, endpoint: &str) {
        if let Some(mut metrics) = self.metrics.get_mut(endpoint) {
            metrics.active_requests += 1;
        }
    }

    pub fn decrement_active_requests(&self, endpoint: &str) {
        if let Some(mut metrics) = self.metrics.get_mut(endpoint) {
            if metrics.active_requests > 0 {
                metrics.active_requests -= 1;
            }
        }
    }

    pub fn get_metrics(&self) -> HashMap<String, serde_json::Value> {
        let mut result = HashMap::new();

        for entry in self.metrics.iter() {
            let endpoint = entry.key();
            let metrics = entry.value();

            let mut endpoint_metrics = HashMap::new();
            endpoint_metrics.insert(
                "latency_ms".to_string(),
                serde_json::Number::from_f64(metrics.latency_ms)
                    .map(serde_json::Value::Number)
                    .unwrap_or_else(|| serde_json::Value::Number(serde_json::Number::from(0))),
            );
            endpoint_metrics.insert(
                "success_rate".to_string(),
                serde_json::Number::from_f64(metrics.success_rate)
                    .map(serde_json::Value::Number)
                    .unwrap_or_else(|| serde_json::Value::Number(serde_json::Number::from(0))),
            );
            endpoint_metrics.insert(
                "cost_per_request".to_string(),
                serde_json::Number::from_f64(metrics.cost_per_request)
                    .map(serde_json::Value::Number)
                    .unwrap_or_else(|| serde_json::Value::Number(serde_json::Number::from(0))),
            );
            endpoint_metrics.insert(
                "active_requests".to_string(),
                serde_json::Value::Number(serde_json::Number::from(metrics.active_requests)),
            );

            result.insert(
                endpoint.clone(),
                serde_json::Value::Object(endpoint_metrics.into_iter().collect()),
            );
        }

        result
    }
}
