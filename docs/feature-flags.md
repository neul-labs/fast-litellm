# Feature Flags Guide

Complete guide to feature flag configuration and deployment strategies in LiteLLM Rust.

## Overview

Feature flags enable safe, gradual rollout of Rust acceleration components with automatic fallback capabilities. They provide fine-grained control over which features are enabled for specific traffic percentages.

## Feature States

### Available States

- **`enabled`**: Feature fully enabled (100% traffic)
- **`disabled`**: Feature completely disabled
- **`canary`**: Small percentage rollout (typically 5-15%)
- **`gradual_rollout`**: Progressive percentage-based rollout
- **`shadow`**: Run in background without affecting responses

### State Transitions

```
disabled → canary → gradual_rollout → enabled
    ↑                                      ↓
    ←─────────── automatic_fallback ───────┘
```

## Configuration Methods

### 1. Environment Variables

Simple on/off control and percentage rollouts:

```bash
# Global disable
export LITELLM_RUST_DISABLE_ALL=true

# Individual feature control
export LITELLM_RUST_RUST_ROUTING=false
export LITELLM_RUST_RUST_TOKEN_COUNTING=true
export LITELLM_RUST_BATCH_TOKEN_COUNTING=canary:10
export LITELLM_RUST_ASYNC_ROUTING=rollout:25

# Configuration file
export LITELLM_RUST_FEATURE_CONFIG=/path/to/config.json

# Alert settings
export LITELLM_RUST_ALERT_FILE=/var/log/litellm_alerts.log
```

### 2. JSON Configuration File

Advanced configuration with thresholds and dependencies:

```json
{
  "features": {
    "rust_routing": {
      "state": "enabled",
      "rollout_percentage": 100.0,
      "error_threshold": 10,
      "performance_threshold_ms": 500.0,
      "fallback_on_error": true
    },
    "rust_token_counting": {
      "state": "enabled",
      "rollout_percentage": 100.0,
      "error_threshold": 5,
      "performance_threshold_ms": 100.0,
      "fallback_on_error": true
    },
    "batch_token_counting": {
      "state": "canary",
      "rollout_percentage": 15.0,
      "error_threshold": 2,
      "performance_threshold_ms": 80.0,
      "dependencies": ["rust_token_counting"]
    },
    "async_routing": {
      "state": "shadow",
      "rollout_percentage": 5.0,
      "error_threshold": 1,
      "performance_threshold_ms": 300.0,
      "dependencies": ["rust_routing"]
    }
  },
  "global_settings": {
    "enable_automatic_degradation": true,
    "enable_performance_alerts": true,
    "metrics_retention_hours": 24
  }
}
```

### 3. Programmatic Control

Runtime feature flag management:

```python
import litellm_rust

# Check feature status
enabled = litellm_rust.is_enabled("rust_routing")
status = litellm_rust.get_feature_status()

# Reset error counts
litellm_rust.reset_errors("rust_routing")
litellm_rust.reset_errors()  # Reset all
```

## Available Features

### Core Features

| Feature | Description | Default State | Typical Rollout |
|---------|-------------|---------------|-----------------|
| `rust_routing` | Advanced request routing | `enabled` | 100% |
| `rust_token_counting` | Fast token counting | `enabled` | 100% |
| `rust_rate_limiting` | Efficient rate limiting | `gradual_rollout` | 75% |
| `rust_connection_pooling` | Connection management | `gradual_rollout` | 50% |

### Advanced Features

| Feature | Description | Default State | Typical Rollout |
|---------|-------------|---------------|-----------------|
| `batch_token_counting` | Batch processing for tokens | `canary` | 10% |
| `async_routing` | Async routing capabilities | `shadow` | 5% |
| `performance_monitoring` | Metrics collection | `enabled` | 100% |

## Deployment Strategies

### 1. Canary Deployment

Start with a small percentage of traffic:

```bash
# Enable for 5% of traffic
export LITELLM_RUST_NEW_FEATURE=canary:5
```

**Benefits**:
- Low risk exposure
- Early problem detection
- Real-world validation

**Monitoring**:
- Error rates < 1%
- Latency within 2x of baseline
- No increase in timeouts

### 2. Gradual Rollout

Progressive percentage increase:

```bash
# Week 1: 10%
export LITELLM_RUST_FEATURE=rollout:10

# Week 2: 25%
export LITELLM_RUST_FEATURE=rollout:25

# Week 3: 50%
export LITELLM_RUST_FEATURE=rollout:50

# Week 4: 100%
export LITELLM_RUST_FEATURE=enabled
```

**Timeline**:
- **Days 1-3**: Monitor metrics closely
- **Days 4-7**: Increase if stable
- **Weeks 2-4**: Progressive rollout
- **Final**: Full deployment

### 3. Shadow Deployment

Run alongside production without affecting responses:

```json
{
  "features": {
    "experimental_feature": {
      "state": "shadow",
      "rollout_percentage": 100.0,
      "fallback_on_error": false
    }
  }
}
```

**Use Cases**:
- Performance validation
- Algorithm comparison
- Load testing

## Automatic Degradation

### Error-Based Degradation

Features automatically disable when error thresholds are exceeded:

```python
# Configuration
{
  "error_threshold": 5,  # Disable after 5 errors
  "fallback_on_error": true
}

# Automatic behavior
# Error 1-4: Continue with Rust
# Error 5: Disable feature, use Python fallback
# Error counts reset after successful operations
```

### Performance-Based Degradation

Features disable when performance thresholds are breached:

```python
# Configuration
{
  "performance_threshold_ms": 100.0,  # 100ms threshold
  "fallback_on_error": true
}

# Automatic behavior
# Latency < 100ms: Continue with Rust
# Latency > 100ms: Disable feature, use Python fallback
```

## Monitoring and Alerts

### Built-in Monitoring

```python
import litellm_rust

# Get feature status
status = litellm_rust.get_feature_status()
print(f"Features enabled: {status['global_status']['enabled_features']}")

# Check specific feature
for feature, data in status['features'].items():
    print(f"{feature}: {data['state']} ({data['rollout_percentage']}%)")
    print(f"  Errors: {data['error_count']}")
    print(f"  Avg latency: {data['avg_performance_ms']:.2f}ms")
```

### Alert Configuration

```bash
# File-based alerts
export LITELLM_RUST_ALERT_FILE=/var/log/litellm_alerts.log

# Alert levels
# - warning: Performance degradation
# - critical: Error threshold exceeded
```

### Custom Monitoring Integration

```python
# Export metrics for external monitoring
metrics = litellm_rust.export_performance_data(format="json")

# Parse and send to monitoring system
import json
data = json.loads(metrics)

# Send to Prometheus, DataDog, etc.
send_to_monitoring_system(data)
```

## Rollout Best Practices

### Pre-Rollout Checklist

- [ ] Feature tested in development
- [ ] Benchmarks show expected improvement
- [ ] Error handling implemented
- [ ] Monitoring configured
- [ ] Rollback plan defined

### During Rollout

1. **Monitor key metrics**:
   - Error rates
   - Latency percentiles (P50, P95, P99)
   - Throughput
   - Memory usage

2. **Set alerts**:
   - Error rate > 1%
   - Latency increase > 50%
   - Memory usage spike

3. **Gradual increase**:
   - Start with 5-10%
   - Double every 2-3 days if stable
   - Monitor for 24 hours at each level

### Post-Rollout

- Monitor for 1 week at 100%
- Document lessons learned
- Update runbooks
- Clean up temporary configurations

## Troubleshooting

### Common Issues

**Feature not enabling**:
```bash
# Check configuration
python -c "import litellm_rust; print(litellm_rust.get_feature_status())"

# Check environment variables
env | grep LITELLM_RUST
```

**Automatic degradation triggered**:
```bash
# Check error counts
python -c "
import litellm_rust
status = litellm_rust.get_feature_status()
for f, d in status['features'].items():
    if d['error_count'] > 0:
        print(f'{f}: {d[\"error_count\"]} errors')
"

# Reset errors
python -c "import litellm_rust; litellm_rust.reset_errors()"
```

**Performance issues**:
```bash
# Check performance metrics
python -c "
import litellm_rust
stats = litellm_rust.get_performance_stats()
for component, data in stats.items():
    print(f'{component}: {data[\"avg_duration_ms\"]}ms avg')
"
```

### Debug Mode

Enable debug logging for detailed information:

```bash
export RUST_LOG=debug
export LITELLM_RUST_DEBUG=true
python -c "import litellm_rust"
```

## Security Considerations

### Configuration Security

- Store sensitive configs in secure locations
- Use environment variables for production
- Rotate configuration access credentials
- Audit configuration changes

### Feature Flag Security

- Validate configuration inputs
- Sanitize feature names
- Limit configuration file permissions
- Monitor for unauthorized changes

Feature flags provide powerful control over the Rust acceleration rollout while maintaining safety and observability. Use them to deploy confidently and iterate quickly while minimizing risk to production systems.