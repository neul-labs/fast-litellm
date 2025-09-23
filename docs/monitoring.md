# Performance Monitoring Guide

Comprehensive guide to monitoring, alerting, and optimizing LiteLLM Rust acceleration performance.

## Overview

The performance monitoring system provides real-time insights into Rust acceleration performance, automatic alerting, and optimization recommendations to ensure optimal operation in production.

## Metrics Collection

### Core Metrics

The system automatically tracks:

| Metric | Description | Units |
|--------|-------------|-------|
| **Latency** | Operation duration | milliseconds |
| **Throughput** | Operations per second | ops/sec |
| **Error Rate** | Percentage of failed operations | % |
| **Success Rate** | Percentage of successful operations | % |
| **Memory Usage** | Component memory consumption | MB |

### Statistical Analysis

For each metric, the system calculates:

- **Average (Mean)**: Overall performance baseline
- **P50 (Median)**: Typical user experience
- **P95**: Good user experience threshold
- **P99**: Outlier detection and capacity planning
- **Min/Max**: Performance boundaries

## Real-Time Monitoring

### Basic Monitoring

```python
import litellm_rust

# Get real-time statistics
stats = litellm_rust.get_performance_stats()

# Display component performance
for component, data in stats.items():
    print(f"\n{component}:")
    print(f"  Average latency: {data['avg_duration_ms']:.2f}ms")
    print(f"  P95 latency: {data['p95_duration_ms']:.2f}ms")
    print(f"  Error rate: {data['error_rate']:.2f}%")
    print(f"  Throughput: {data['throughput_per_second']:.2f} ops/sec")
    print(f"  Total calls: {data['total_calls']}")
```

### Component-Specific Monitoring

```python
# Monitor specific component
routing_stats = litellm_rust.get_performance_stats("rust_routing")
token_stats = litellm_rust.get_performance_stats("rust_token_counting")

# Check component health
if routing_stats['error_rate'] > 5.0:
    print("⚠️ High error rate in routing component")

if token_stats['avg_duration_ms'] > 100.0:
    print("⚠️ High latency in token counting")
```

### Continuous Monitoring

```python
import time
import threading

def monitor_performance():
    """Background monitoring with alerts."""
    while True:
        try:
            stats = litellm_rust.get_performance_stats()

            for component, data in stats.items():
                # Check thresholds
                if data['error_rate'] > 5.0:
                    alert(f"High error rate: {component} at {data['error_rate']:.2f}%")

                if data['avg_duration_ms'] > 1000.0:
                    alert(f"High latency: {component} at {data['avg_duration_ms']:.2f}ms")

            time.sleep(60)  # Check every minute

        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(5)

# Start background monitoring
monitor_thread = threading.Thread(target=monitor_performance, daemon=True)
monitor_thread.start()
```

## Performance Comparison

### Rust vs Python Comparison

```python
# Compare implementations
comparison = litellm_rust.compare_implementations(
    "rust_routing",
    "python_routing"
)

print("Performance Comparison:")
print(f"Speed improvement: {comparison['speed_improvement']['avg_latency']:.2f}x")
print(f"P95 improvement: {comparison['speed_improvement']['p95_latency']:.2f}x")
print(f"Throughput improvement: {comparison['speed_improvement']['throughput']:.2f}x")
print(f"Reliability improvement: {comparison['reliability']['reliability_improvement']:.2f}%")
```

### Benchmark Tracking

```python
def run_performance_benchmark():
    """Run standardized performance benchmark."""
    import time

    # Token counting benchmark
    texts = ["Sample text for benchmarking"] * 100

    start_time = time.perf_counter()
    for text in texts:
        # This will be accelerated if enabled
        litellm.token_counter(text, "gpt-3.5-turbo")

    duration = (time.perf_counter() - start_time) * 1000

    # Record benchmark result
    litellm_rust.record_performance(
        component="benchmark_token_counting",
        operation="batch_100",
        duration_ms=duration,
        input_size=len(texts),
        metadata={"benchmark": True}
    )

    return duration

# Run weekly benchmarks
weekly_benchmark = run_performance_benchmark()
print(f"Weekly benchmark: {weekly_benchmark:.2f}ms for 100 operations")
```

## Alerting System

### Built-in Alerts

The system provides automatic alerts for:

1. **High Error Rate**: > 5% failures
2. **High Latency**: > threshold for component
3. **Low Throughput**: < expected operations/second
4. **Memory Issues**: Excessive memory usage
5. **Feature Degradation**: Automatic fallback triggered

### Alert Configuration

```python
# Environment-based alert configuration
import os

os.environ['LITELLM_RUST_ALERT_FILE'] = '/var/log/litellm_alerts.log'

# Alerts are automatically written to the file:
# {
#   "timestamp": "2024-01-15T10:30:00Z",
#   "severity": "warning",
#   "component": "rust_routing",
#   "message": "High latency detected",
#   "current_value": 750.5,
#   "threshold": 500.0
# }
```

### Custom Alert Handlers

```python
import json
import logging

def setup_custom_alerting():
    """Set up custom alert processing."""

    alert_file = "/var/log/litellm_alerts.log"

    # Monitor alert file
    def process_alerts():
        try:
            with open(alert_file, 'r') as f:
                for line in f:
                    if line.strip():
                        alert = json.loads(line)
                        handle_alert(alert)
        except FileNotFoundError:
            pass  # No alerts yet

    def handle_alert(alert):
        """Process individual alert."""
        severity = alert['severity']
        component = alert['component']
        message = alert['message']

        if severity == 'critical':
            # Send to PagerDuty, Slack, etc.
            send_critical_alert(component, message)
        elif severity == 'warning':
            # Log or send to monitoring dashboard
            logging.warning(f"LiteLLM Alert: {component} - {message}")

    # Run periodically
    import threading
    import time

    def alert_processor():
        while True:
            process_alerts()
            time.sleep(30)  # Check every 30 seconds

    thread = threading.Thread(target=alert_processor, daemon=True)
    thread.start()

setup_custom_alerting()
```

## Optimization Recommendations

### Automated Recommendations

```python
# Get optimization recommendations
recommendations = litellm_rust.get_recommendations()

for rec in recommendations:
    print(f"\n{rec['type'].upper()} - {rec['severity']}")
    print(f"Component: {rec['component']}")
    print(f"Issue: {rec['message']}")
    print("Suggestions:")
    for suggestion in rec['suggestions']:
        print(f"  • {suggestion}")
```

### Performance Tuning

Based on monitoring data, the system provides recommendations for:

#### High Latency Issues

```python
# Automatic detection and recommendations
{
  "type": "high_latency",
  "severity": "warning",
  "component": "rust_token_counting",
  "message": "Average latency: 150ms exceeds 100ms threshold",
  "suggestions": [
    "Increase token cache size (LITELLM_RUST_TOKEN_CACHE_SIZE)",
    "Enable batch processing for multiple texts",
    "Check for memory pressure",
    "Verify model encoding cache hit rate"
  ]
}
```

#### High Error Rate Issues

```python
{
  "type": "high_error_rate",
  "severity": "critical",
  "component": "rust_routing",
  "message": "Error rate: 7.5% exceeds 5% threshold",
  "suggestions": [
    "Check deployment health status",
    "Verify network connectivity",
    "Review error patterns in logs",
    "Consider temporary feature disable"
  ]
}
```

#### Low Throughput Issues

```python
{
  "type": "low_throughput",
  "severity": "warning",
  "component": "rust_connection_pooling",
  "message": "Throughput: 8 ops/sec below expected 15 ops/sec",
  "suggestions": [
    "Increase connection pool size",
    "Enable HTTP/2 multiplexing",
    "Check for connection timeouts",
    "Review load balancing configuration"
  ]
}
```

## Data Export and Integration

### Export Formats

```python
# Export as JSON for analysis
json_data = litellm_rust.export_performance_data(format="json")

# Export as CSV for spreadsheets
csv_data = litellm_rust.export_performance_data(format="csv")

# Export specific component
routing_data = litellm_rust.export_performance_data(
    component="rust_routing",
    format="json"
)
```

### Integration with External Systems

#### Prometheus Integration

```python
# Export metrics for Prometheus
def export_to_prometheus():
    stats = litellm_rust.get_performance_stats()

    metrics = []
    for component, data in stats.items():
        metrics.extend([
            f'litellm_rust_latency_avg{{component="{component}"}} {data["avg_duration_ms"]}',
            f'litellm_rust_latency_p95{{component="{component}"}} {data["p95_duration_ms"]}',
            f'litellm_rust_error_rate{{component="{component}"}} {data["error_rate"]}',
            f'litellm_rust_throughput{{component="{component}"}} {data["throughput_per_second"]}',
        ])

    return '\n'.join(metrics)

# Write to Prometheus text file
with open('/var/lib/prometheus/node-exporter/litellm_rust.prom', 'w') as f:
    f.write(export_to_prometheus())
```

#### DataDog Integration

```python
import datadog

def send_to_datadog():
    """Send metrics to DataDog."""
    stats = litellm_rust.get_performance_stats()

    for component, data in stats.items():
        datadog.statsd.gauge(
            f'litellm.rust.latency.avg',
            data['avg_duration_ms'],
            tags=[f'component:{component}']
        )
        datadog.statsd.gauge(
            f'litellm.rust.error_rate',
            data['error_rate'],
            tags=[f'component:{component}']
        )
```

#### Custom Webhook Integration

```python
import requests
import json

def send_metrics_webhook(webhook_url):
    """Send metrics to custom webhook."""
    stats = litellm_rust.get_performance_stats()

    payload = {
        "timestamp": datetime.now().isoformat(),
        "service": "litellm-rust",
        "metrics": stats
    }

    response = requests.post(
        webhook_url,
        json=payload,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        print(f"Failed to send metrics: {response.status_code}")
```

## Dashboards and Visualization

### Simple CLI Dashboard

```python
import time
import os

def show_dashboard():
    """Display real-time performance dashboard."""
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')

        print("🚀 LiteLLM Rust Performance Dashboard")
        print("=" * 50)

        stats = litellm_rust.get_performance_stats()

        for component, data in stats.items():
            status = "🟢" if data['error_rate'] < 1 else "🟡" if data['error_rate'] < 5 else "🔴"

            print(f"\n{status} {component}")
            print(f"   Latency: {data['avg_duration_ms']:.1f}ms (P95: {data['p95_duration_ms']:.1f}ms)")
            print(f"   Errors:  {data['error_rate']:.1f}% ({data['failed_calls']}/{data['total_calls']})")
            print(f"   Throughput: {data['throughput_per_second']:.1f} ops/sec")

        # Show recommendations
        recommendations = litellm_rust.get_recommendations()
        if recommendations:
            print(f"\n⚠️  {len(recommendations)} Recommendations:")
            for rec in recommendations[:3]:  # Show top 3
                print(f"   • {rec['component']}: {rec['message']}")

        print(f"\nLast updated: {datetime.now().strftime('%H:%M:%S')}")
        print("Press Ctrl+C to exit")

        time.sleep(5)

# Run dashboard
show_dashboard()
```

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "LiteLLM Rust Performance",
    "panels": [
      {
        "title": "Latency by Component",
        "type": "graph",
        "targets": [
          {
            "expr": "litellm_rust_latency_avg",
            "legendFormat": "{{component}} - Average"
          },
          {
            "expr": "litellm_rust_latency_p95",
            "legendFormat": "{{component}} - P95"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "litellm_rust_error_rate",
            "legendFormat": "{{component}}"
          }
        ]
      },
      {
        "title": "Throughput",
        "type": "graph",
        "targets": [
          {
            "expr": "litellm_rust_throughput",
            "legendFormat": "{{component}}"
          }
        ]
      }
    ]
  }
}
```

## Troubleshooting Performance Issues

### Common Performance Problems

#### High Latency

```python
def diagnose_high_latency(component):
    """Diagnose high latency issues."""
    stats = litellm_rust.get_performance_stats(component)

    if stats['avg_duration_ms'] > 1000:
        print(f"⚠️ High latency detected in {component}")

        # Check specific issues
        if component == "rust_token_counting":
            print("Possible causes:")
            print("- Cache misses (check cache hit rate)")
            print("- Large input texts")
            print("- Memory pressure")
            print("Recommendations:")
            print("- Increase cache size")
            print("- Enable batch processing")

        elif component == "rust_routing":
            print("Possible causes:")
            print("- Unhealthy deployments")
            print("- Network latency")
            print("- Lock contention")
            print("Recommendations:")
            print("- Check deployment health")
            print("- Verify routing strategy")
```

#### Memory Issues

```python
def check_memory_usage():
    """Check for memory-related issues."""
    import psutil

    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024

    print(f"Current memory usage: {memory_mb:.1f} MB")

    if memory_mb > 500:  # High memory usage
        print("⚠️ High memory usage detected")
        print("Recommendations:")
        print("- Reduce token cache size")
        print("- Check for memory leaks")
        print("- Monitor GC patterns")
```

This comprehensive monitoring system provides the visibility and control needed to operate Rust acceleration safely and efficiently in production environments.