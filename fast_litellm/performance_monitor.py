"""
Advanced performance monitoring for LiteLLM Rust acceleration.

This module provides comprehensive performance monitoring with metrics collection,
alerting, and automatic optimization recommendations.
"""

import json
import logging
import os
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""

    component: str
    operation: str
    duration_ms: float
    timestamp: datetime
    success: bool
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ComponentStats:
    """Aggregated statistics for a component."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    throughput_per_second: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = None


@dataclass
class PerformanceAlert:
    """Performance alert definition."""

    component: str
    threshold_type: str  # 'latency', 'error_rate', 'throughput'
    threshold_value: float
    duration_seconds: int
    message: str
    severity: str  # 'warning', 'critical'


class PerformanceMonitor:
    """
    Advanced performance monitoring system for LiteLLM Rust acceleration.

    Features:
    - Real-time metric collection
    - Statistical analysis
    - Performance alerting
    - Automatic optimization recommendations
    - Export capabilities
    """

    def __init__(
        self,
        max_metrics_per_component: int = 10000,
        retention_hours: int = 24,
        enable_alerts: bool = True,
    ):
        self.max_metrics_per_component = max_metrics_per_component
        self.retention_hours = retention_hours
        self.enable_alerts = enable_alerts

        # Thread-safe storage
        self._lock = threading.RLock()
        self._metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_metrics_per_component)
        )
        self._component_stats: Dict[str, ComponentStats] = defaultdict(ComponentStats)
        self._alerts: List[PerformanceAlert] = []
        self._alert_history: List[Dict[str, Any]] = []

        # Performance comparison baseline (Python vs Rust)
        self._baseline_stats: Dict[str, ComponentStats] = {}

        # Background cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_old_metrics, daemon=True
        )
        self._cleanup_thread.start()

        # Default alerts
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Setup default performance alerts."""
        default_alerts = [
            PerformanceAlert(
                component="rust_routing",
                threshold_type="latency",
                threshold_value=500.0,  # 500ms
                duration_seconds=60,
                message="Rust routing latency exceeded 500ms for 1 minute",
                severity="warning",
            ),
            PerformanceAlert(
                component="rust_token_counting",
                threshold_type="latency",
                threshold_value=100.0,  # 100ms
                duration_seconds=30,
                message="Rust token counting latency exceeded 100ms for 30 seconds",
                severity="warning",
            ),
            PerformanceAlert(
                component="rust_routing",
                threshold_type="error_rate",
                threshold_value=5.0,  # 5%
                duration_seconds=120,
                message="Rust routing error rate exceeded 5% for 2 minutes",
                severity="critical",
            ),
            PerformanceAlert(
                component="rust_token_counting",
                threshold_type="error_rate",
                threshold_value=2.0,  # 2%
                duration_seconds=60,
                message="Rust token counting error rate exceeded 2% for 1 minute",
                severity="critical",
            ),
        ]

        with self._lock:
            self._alerts.extend(default_alerts)

    def record_metric(
        self,
        component: str,
        operation: str,
        duration_ms: float,
        success: bool = True,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Record a performance metric.

        Args:
            component: Component name (e.g., 'rust_routing', 'python_routing')
            operation: Operation name (e.g., 'route_request', 'count_tokens')
            duration_ms: Duration in milliseconds
            success: Whether the operation was successful
            input_size: Optional input size in bytes or tokens
            output_size: Optional output size in bytes or tokens
            metadata: Additional metadata
        """
        metric = PerformanceMetric(
            component=component,
            operation=operation,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            success=success,
            input_size=input_size,
            output_size=output_size,
            metadata=metadata or {},
        )

        with self._lock:
            self._metrics[component].append(metric)
            self._update_component_stats(component)

        # Check alerts if enabled
        if self.enable_alerts:
            self._check_alerts(component)

    def _update_component_stats(self, component: str):
        """Update aggregated statistics for a component."""
        metrics = list(self._metrics[component])
        if not metrics:
            return

        # Filter metrics from last hour for real-time stats
        now = datetime.now()
        recent_metrics = [
            m for m in metrics if (now - m.timestamp).total_seconds() <= 3600
        ]

        if not recent_metrics:
            return

        stats = self._component_stats[component]
        stats.total_calls = len(recent_metrics)
        stats.successful_calls = sum(1 for m in recent_metrics if m.success)
        stats.failed_calls = stats.total_calls - stats.successful_calls

        durations = [m.duration_ms for m in recent_metrics]
        stats.avg_duration_ms = statistics.mean(durations)
        stats.min_duration_ms = min(durations)
        stats.max_duration_ms = max(durations)

        # Calculate percentiles
        if len(durations) >= 20:  # Only calculate percentiles with sufficient data
            sorted_durations = sorted(durations)
            stats.p95_duration_ms = sorted_durations[int(0.95 * len(sorted_durations))]
            stats.p99_duration_ms = sorted_durations[int(0.99 * len(sorted_durations))]

        # Calculate throughput (calls per second)
        time_span = (now - recent_metrics[0].timestamp).total_seconds()
        if time_span > 0:
            stats.throughput_per_second = len(recent_metrics) / time_span

        # Calculate error rate
        stats.error_rate = (
            (stats.failed_calls / stats.total_calls) * 100
            if stats.total_calls > 0
            else 0
        )

        stats.last_updated = now

    def _check_alerts(self, component: str):
        """Check if any alerts should be triggered for a component."""
        if not self.enable_alerts:
            return

        stats = self._component_stats.get(component)
        if not stats:
            return

        for alert in self._alerts:
            if alert.component != component:
                continue

            should_alert = False
            current_value = 0

            if alert.threshold_type == "latency":
                current_value = stats.avg_duration_ms
                should_alert = current_value > alert.threshold_value
            elif alert.threshold_type == "error_rate":
                current_value = stats.error_rate
                should_alert = current_value > alert.threshold_value
            elif alert.threshold_type == "throughput":
                current_value = stats.throughput_per_second
                should_alert = current_value < alert.threshold_value

            if should_alert:
                self._trigger_alert(alert, current_value)

    def _trigger_alert(self, alert: PerformanceAlert, current_value: float):
        """Trigger a performance alert."""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "component": alert.component,
            "threshold_type": alert.threshold_type,
            "threshold_value": alert.threshold_value,
            "current_value": current_value,
            "message": alert.message,
            "severity": alert.severity,
        }

        with self._lock:
            self._alert_history.append(alert_data)

        logger.warning(
            f"Performance Alert [{alert.severity.upper()}]: {alert.message} "
            f"(current: {current_value:.2f}, threshold: {alert.threshold_value:.2f})"
        )

        # Write to alert file if configured
        alert_file = os.environ.get("LITELLM_RUST_ALERT_FILE")
        if alert_file:
            try:
                with open(alert_file, "a") as f:
                    f.write(json.dumps(alert_data) + "\n")
            except Exception as e:
                logger.error(f"Failed to write alert to file {alert_file}: {e}")

    def _cleanup_old_metrics(self):
        """Background thread to clean up old metrics."""
        while True:
            try:
                time.sleep(3600)  # Run every hour
                cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

                with self._lock:
                    for component in self._metrics:
                        # Remove old metrics
                        metrics = self._metrics[component]
                        while metrics and metrics[0].timestamp < cutoff_time:
                            metrics.popleft()

                    # Clean up old alerts
                    self._alert_history = [
                        alert
                        for alert in self._alert_history[
                            -1000:
                        ]  # Keep last 1000 alerts
                        if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
                    ]

            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")

    def get_component_stats(self, component: str) -> Optional[ComponentStats]:
        """Get statistics for a specific component."""
        with self._lock:
            return self._component_stats.get(component)

    def get_all_stats(self) -> Dict[str, ComponentStats]:
        """Get statistics for all components."""
        with self._lock:
            return dict(self._component_stats)

    def compare_performance(
        self, rust_component: str, python_component: str
    ) -> Dict[str, Any]:
        """
        Compare performance between Rust and Python implementations.

        Args:
            rust_component: Name of the Rust component
            python_component: Name of the Python component

        Returns:
            Comparison metrics
        """
        with self._lock:
            rust_stats = self._component_stats.get(rust_component)
            python_stats = self._component_stats.get(python_component)

            if not rust_stats or not python_stats:
                return {"error": "Insufficient data for comparison"}

            comparison = {
                "rust_component": rust_component,
                "python_component": python_component,
                "speed_improvement": {
                    "avg_latency": (
                        python_stats.avg_duration_ms / rust_stats.avg_duration_ms
                        if rust_stats.avg_duration_ms > 0
                        else 0
                    ),
                    "p95_latency": (
                        python_stats.p95_duration_ms / rust_stats.p95_duration_ms
                        if rust_stats.p95_duration_ms > 0
                        else 0
                    ),
                    "throughput": (
                        rust_stats.throughput_per_second
                        / python_stats.throughput_per_second
                        if python_stats.throughput_per_second > 0
                        else 0
                    ),
                },
                "reliability": {
                    "rust_error_rate": rust_stats.error_rate,
                    "python_error_rate": python_stats.error_rate,
                    "reliability_improvement": python_stats.error_rate
                    - rust_stats.error_rate,
                },
                "rust_stats": asdict(rust_stats),
                "python_stats": asdict(python_stats),
            }

            return comparison

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate optimization recommendations based on performance data.

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        with self._lock:
            for component, stats in self._component_stats.items():
                if not stats.last_updated:
                    continue

                # High latency recommendation
                if stats.avg_duration_ms > 1000:  # > 1 second
                    recommendations.append(
                        {
                            "component": component,
                            "type": "high_latency",
                            "severity": (
                                "warning"
                                if stats.avg_duration_ms < 5000
                                else "critical"
                            ),
                            "message": f"High average latency: {stats.avg_duration_ms:.2f}ms",
                            "suggestions": [
                                "Consider enabling batch processing if available",
                                "Check for inefficient algorithms",
                                "Verify cache hit rates",
                            ],
                        }
                    )

                # High error rate recommendation
                if stats.error_rate > 5.0:  # > 5%
                    recommendations.append(
                        {
                            "component": component,
                            "type": "high_error_rate",
                            "severity": "critical",
                            "message": f"High error rate: {stats.error_rate:.2f}%",
                            "suggestions": [
                                "Investigate common error patterns",
                                "Consider disabling Rust acceleration temporarily",
                                "Review input validation",
                            ],
                        }
                    )

                # Low throughput recommendation
                if stats.throughput_per_second < 10 and stats.total_calls > 100:
                    recommendations.append(
                        {
                            "component": component,
                            "type": "low_throughput",
                            "severity": "warning",
                            "message": f"Low throughput: {stats.throughput_per_second:.2f} ops/sec",
                            "suggestions": [
                                "Enable parallel processing",
                                "Consider connection pooling",
                                "Review resource constraints",
                            ],
                        }
                    )

        return recommendations

    def export_metrics(
        self,
        component: Optional[str] = None,
        format: str = "json",
        include_raw_metrics: bool = False,
    ) -> str:
        """
        Export performance metrics.

        Args:
            component: Specific component to export (None for all)
            format: Export format ('json', 'csv')
            include_raw_metrics: Whether to include raw metric data

        Returns:
            Exported data as string
        """
        with self._lock:
            if component:
                components = (
                    {component: self._component_stats.get(component)}
                    if component in self._component_stats
                    else {}
                )
                raw_metrics = (
                    {component: list(self._metrics.get(component, []))}
                    if include_raw_metrics
                    else {}
                )
            else:
                components = dict(self._component_stats)
                raw_metrics = (
                    {comp: list(metrics) for comp, metrics in self._metrics.items()}
                    if include_raw_metrics
                    else {}
                )

            export_data = {
                "timestamp": datetime.now().isoformat(),
                "component_stats": {
                    comp: asdict(stats) for comp, stats in components.items() if stats
                },
                "alert_history": self._alert_history[-100:],  # Last 100 alerts
                "recommendations": self.get_optimization_recommendations(),
            }

            if include_raw_metrics:
                export_data["raw_metrics"] = {
                    comp: [asdict(metric) for metric in metrics]
                    for comp, metrics in raw_metrics.items()
                }

            if format == "json":
                return json.dumps(export_data, indent=2, default=str)
            elif format == "csv":
                # Simple CSV export for component stats
                import csv
                import io

                output = io.StringIO()
                writer = csv.writer(output)

                # Write header
                writer.writerow(
                    [
                        "component",
                        "total_calls",
                        "successful_calls",
                        "failed_calls",
                        "avg_duration_ms",
                        "p95_duration_ms",
                        "throughput_per_second",
                        "error_rate",
                    ]
                )

                # Write data
                for comp, stats in components.items():
                    if stats:
                        writer.writerow(
                            [
                                comp,
                                stats.total_calls,
                                stats.successful_calls,
                                stats.failed_calls,
                                stats.avg_duration_ms,
                                stats.p95_duration_ms,
                                stats.throughput_per_second,
                                stats.error_rate,
                            ]
                        )

                return output.getvalue()

            else:
                raise ValueError(f"Unsupported format: {format}")

    def reset_metrics(self, component: Optional[str] = None):
        """Reset metrics for a component or all components."""
        with self._lock:
            if component:
                if component in self._metrics:
                    self._metrics[component].clear()
                if component in self._component_stats:
                    del self._component_stats[component]
            else:
                self._metrics.clear()
                self._component_stats.clear()
                self._alert_history.clear()


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def record_performance(
    component: str, operation: str, duration_ms: float, success: bool = True, **kwargs
) -> None:
    """Record a performance metric."""
    _performance_monitor.record_metric(
        component, operation, duration_ms, success, **kwargs
    )


def get_stats(component: Optional[str] = None) -> Dict[str, Any]:
    """Get performance statistics."""
    if component:
        stats = _performance_monitor.get_component_stats(component)
        return asdict(stats) if stats else {}
    else:
        return {
            comp: asdict(stats)
            for comp, stats in _performance_monitor.get_all_stats().items()
        }


def compare_implementations(
    rust_component: str, python_component: str
) -> Dict[str, Any]:
    """Compare Rust vs Python implementation performance."""
    return _performance_monitor.compare_performance(rust_component, python_component)


def get_recommendations() -> List[Dict[str, Any]]:
    """Get optimization recommendations."""
    return _performance_monitor.get_optimization_recommendations()


def export_performance_data(
    component: Optional[str] = None, format: str = "json"
) -> str:
    """Export performance data."""
    return _performance_monitor.export_metrics(component, format)


def reset_performance_data(component: Optional[str] = None):
    """Reset performance data."""
    _performance_monitor.reset_metrics(component)
