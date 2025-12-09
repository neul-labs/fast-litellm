use dashmap::DashMap;
/// Performance monitoring and metrics collection
use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
pub struct PerformanceMetric {
    pub component: String,
    pub operation: String,
    pub duration_ms: f64,
    pub success: bool,
    pub input_size: Option<usize>,
    pub output_size: Option<usize>,
    pub timestamp: u64,
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

#[derive(Debug)]
pub struct ComponentStats {
    pub total_calls: AtomicU64,
    pub total_duration_ms: AtomicU64,
    pub success_count: AtomicU64,
    pub error_count: AtomicU64,
    pub min_duration_ms: AtomicU64,
    pub max_duration_ms: AtomicU64,
}

impl Default for ComponentStats {
    fn default() -> Self {
        Self::new()
    }
}

impl ComponentStats {
    pub fn new() -> Self {
        Self {
            total_calls: AtomicU64::new(0),
            total_duration_ms: AtomicU64::new(0),
            success_count: AtomicU64::new(0),
            error_count: AtomicU64::new(0),
            min_duration_ms: AtomicU64::new(u64::MAX),
            max_duration_ms: AtomicU64::new(0),
        }
    }

    pub fn update(&self, duration_ms: f64, success: bool) {
        let duration_int = (duration_ms * 1000.0) as u64; // Store as microseconds for precision

        self.total_calls.fetch_add(1, Ordering::Relaxed);
        self.total_duration_ms
            .fetch_add(duration_int, Ordering::Relaxed);

        if success {
            self.success_count.fetch_add(1, Ordering::Relaxed);
        } else {
            self.error_count.fetch_add(1, Ordering::Relaxed);
        }

        // Update min/max with proper atomic operations
        let mut current_min = self.min_duration_ms.load(Ordering::Relaxed);
        while duration_int < current_min {
            match self.min_duration_ms.compare_exchange_weak(
                current_min,
                duration_int,
                Ordering::Relaxed,
                Ordering::Relaxed,
            ) {
                Ok(_) => break,
                Err(new_min) => current_min = new_min,
            }
        }

        let mut current_max = self.max_duration_ms.load(Ordering::Relaxed);
        while duration_int > current_max {
            match self.max_duration_ms.compare_exchange_weak(
                current_max,
                duration_int,
                Ordering::Relaxed,
                Ordering::Relaxed,
            ) {
                Ok(_) => break,
                Err(new_max) => current_max = new_max,
            }
        }
    }

    pub fn to_json(&self) -> serde_json::Value {
        let total_calls = self.total_calls.load(Ordering::Relaxed);
        let total_duration = self.total_duration_ms.load(Ordering::Relaxed);
        let success_count = self.success_count.load(Ordering::Relaxed);
        let error_count = self.error_count.load(Ordering::Relaxed);
        let min_duration = self.min_duration_ms.load(Ordering::Relaxed);
        let max_duration = self.max_duration_ms.load(Ordering::Relaxed);

        let avg_duration = if total_calls > 0 {
            (total_duration as f64) / (total_calls as f64) / 1000.0 // Convert back to milliseconds
        } else {
            0.0
        };

        let success_rate = if total_calls > 0 {
            (success_count as f64) / (total_calls as f64)
        } else {
            0.0
        };

        serde_json::json!({
            "total_calls": total_calls,
            "average_duration_ms": avg_duration,
            "success_rate": success_rate,
            "error_count": error_count,
            "min_duration_ms": if min_duration == u64::MAX { 0.0 } else { (min_duration as f64) / 1000.0 },
            "max_duration_ms": (max_duration as f64) / 1000.0,
            "total_duration_ms": (total_duration as f64) / 1000.0
        })
    }
}

pub struct PerformanceMonitor {
    metrics: DashMap<String, Vec<PerformanceMetric>>,
    component_stats: DashMap<String, ComponentStats>,
}

impl Default for PerformanceMonitor {
    fn default() -> Self {
        Self::new()
    }
}

impl PerformanceMonitor {
    pub fn new() -> Self {
        Self {
            metrics: DashMap::new(),
            component_stats: DashMap::new(),
        }
    }

    pub fn record(&self, metric: PerformanceMetric) {
        let key = format!("{}:{}", metric.component, metric.operation);

        // Update component stats
        let stats = self
            .component_stats
            .entry(metric.component.clone())
            .or_default();
        stats.update(metric.duration_ms, metric.success);

        // Store detailed metric (limit to last 1000 entries per key)
        let mut metrics = self.metrics.entry(key).or_default();
        metrics.push(metric);
        if metrics.len() > 1000 {
            metrics.remove(0);
        }
    }

    pub fn get_stats(&self, component: Option<&str>) -> HashMap<String, serde_json::Value> {
        let mut result = HashMap::new();

        if let Some(comp) = component {
            if let Some(stats) = self.component_stats.get(comp) {
                result.insert(comp.to_string(), stats.to_json());
            }
        } else {
            for entry in self.component_stats.iter() {
                result.insert(entry.key().clone(), entry.value().to_json());
            }
        }

        result
    }

    pub fn compare_implementations(
        &self,
        rust_component: &str,
        python_component: &str,
    ) -> HashMap<String, serde_json::Value> {
        let mut comparison = HashMap::new();

        if let (Some(rust_stats), Some(python_stats)) = (
            self.component_stats.get(rust_component),
            self.component_stats.get(python_component),
        ) {
            let rust_json = rust_stats.to_json();
            let python_json = python_stats.to_json();

            if let (Some(rust_avg), Some(python_avg)) = (
                rust_json
                    .get("average_duration_ms")
                    .and_then(|v| v.as_f64()),
                python_json
                    .get("average_duration_ms")
                    .and_then(|v| v.as_f64()),
            ) {
                let speedup = if rust_avg > 0.0 {
                    python_avg / rust_avg
                } else {
                    0.0
                };

                comparison.insert("rust".to_string(), rust_json);
                comparison.insert("python".to_string(), python_json);
                comparison.insert(
                    "speedup".to_string(),
                    serde_json::Number::from_f64(speedup)
                        .map(serde_json::Value::Number)
                        .unwrap_or_else(|| serde_json::Value::Number(serde_json::Number::from(0))),
                );
                comparison.insert(
                    "improvement_percentage".to_string(),
                    serde_json::Number::from_f64((speedup - 1.0) * 100.0)
                        .map(serde_json::Value::Number)
                        .unwrap_or_else(|| serde_json::Value::Number(serde_json::Number::from(0))),
                );
            }
        }

        comparison
    }

    pub fn get_recommendations(&self) -> Vec<HashMap<String, serde_json::Value>> {
        let mut recommendations = Vec::new();

        for entry in self.component_stats.iter() {
            let component = entry.key();
            let stats = entry.value();

            let total_calls = stats.total_calls.load(Ordering::Relaxed);
            let error_count = stats.error_count.load(Ordering::Relaxed);
            let avg_duration = if total_calls > 0 {
                (stats.total_duration_ms.load(Ordering::Relaxed) as f64)
                    / (total_calls as f64)
                    / 1000.0
            } else {
                0.0
            };

            // High error rate recommendation
            if total_calls > 100 && error_count as f64 / total_calls as f64 > 0.05 {
                let mut rec = HashMap::new();
                rec.insert(
                    "type".to_string(),
                    serde_json::Value::String("high_error_rate".to_string()),
                );
                rec.insert(
                    "component".to_string(),
                    serde_json::Value::String(component.clone()),
                );
                rec.insert(
                    "description".to_string(),
                    serde_json::Value::String(format!(
                        "Component {} has high error rate: {:.1}%",
                        component,
                        (error_count as f64 / total_calls as f64) * 100.0
                    )),
                );
                rec.insert(
                    "priority".to_string(),
                    serde_json::Value::String("high".to_string()),
                );
                rec.insert("suggestion".to_string(), serde_json::Value::String(
                    "Consider investigating error causes or implementing circuit breaker pattern".to_string()
                ));
                recommendations.push(rec);
            }

            // Slow performance recommendation
            if avg_duration > 1000.0 {
                // > 1 second average
                let mut rec = HashMap::new();
                rec.insert(
                    "type".to_string(),
                    serde_json::Value::String("slow_performance".to_string()),
                );
                rec.insert(
                    "component".to_string(),
                    serde_json::Value::String(component.clone()),
                );
                rec.insert(
                    "description".to_string(),
                    serde_json::Value::String(format!(
                        "Component {} has slow average response time: {:.1}ms",
                        component, avg_duration
                    )),
                );
                rec.insert(
                    "priority".to_string(),
                    serde_json::Value::String("medium".to_string()),
                );
                rec.insert(
                    "suggestion".to_string(),
                    serde_json::Value::String(
                        "Consider optimizing algorithms or increasing concurrency".to_string(),
                    ),
                );
                recommendations.push(rec);
            }

            // Low usage recommendation
            if total_calls < 10 {
                let mut rec = HashMap::new();
                rec.insert(
                    "type".to_string(),
                    serde_json::Value::String("low_usage".to_string()),
                );
                rec.insert(
                    "component".to_string(),
                    serde_json::Value::String(component.clone()),
                );
                rec.insert(
                    "description".to_string(),
                    serde_json::Value::String(format!(
                        "Component {} has very low usage: {} calls",
                        component, total_calls
                    )),
                );
                rec.insert(
                    "priority".to_string(),
                    serde_json::Value::String("low".to_string()),
                );
                rec.insert(
                    "suggestion".to_string(),
                    serde_json::Value::String(
                        "Consider if this component is needed or increase feature flag percentage"
                            .to_string(),
                    ),
                );
                recommendations.push(rec);
            }
        }

        recommendations
    }

    pub fn export_data(&self, component: Option<&str>, format: &str) -> String {
        let stats = self.get_stats(component);

        match format {
            "json" => serde_json::to_string_pretty(&stats).unwrap_or_default(),
            "csv" => {
                let mut csv = String::from(
                    "component,total_calls,average_duration_ms,success_rate,error_count\n",
                );
                for (comp, data) in stats {
                    if let serde_json::Value::Object(obj) = data {
                        csv.push_str(&format!(
                            "{},{},{},{},{}\n",
                            comp,
                            obj.get("total_calls").and_then(|v| v.as_u64()).unwrap_or(0),
                            obj.get("average_duration_ms")
                                .and_then(|v| v.as_f64())
                                .unwrap_or(0.0),
                            obj.get("success_rate")
                                .and_then(|v| v.as_f64())
                                .unwrap_or(0.0),
                            obj.get("error_count").and_then(|v| v.as_u64()).unwrap_or(0)
                        ));
                    }
                }
                csv
            }
            _ => serde_json::to_string_pretty(&stats).unwrap_or_default(),
        }
    }
}

// Global performance monitor
lazy_static::lazy_static! {
    static ref PERFORMANCE_MONITOR: PerformanceMonitor = PerformanceMonitor::new();
}

pub fn record_performance(
    component: &str,
    operation: &str,
    duration_ms: f64,
    success: bool,
    input_size: Option<usize>,
    output_size: Option<usize>,
    metadata: Option<HashMap<String, serde_json::Value>>,
) {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64;

    let metric = PerformanceMetric {
        component: component.to_string(),
        operation: operation.to_string(),
        duration_ms,
        success,
        input_size,
        output_size,
        timestamp,
        metadata,
    };

    PERFORMANCE_MONITOR.record(metric);
}

pub fn get_performance_stats(component: Option<&str>) -> HashMap<String, serde_json::Value> {
    PERFORMANCE_MONITOR.get_stats(component)
}

pub fn compare_implementations(
    rust_component: &str,
    python_component: &str,
) -> HashMap<String, serde_json::Value> {
    PERFORMANCE_MONITOR.compare_implementations(rust_component, python_component)
}

pub fn get_recommendations() -> Vec<HashMap<String, serde_json::Value>> {
    PERFORMANCE_MONITOR.get_recommendations()
}

pub fn export_performance_data(component: Option<&str>, format: &str) -> String {
    PERFORMANCE_MONITOR.export_data(component, format)
}
