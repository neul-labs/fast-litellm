# Configuration Guide

Complete configuration reference for LiteLLM Rust acceleration.

## Environment Variables

### Global Controls

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LITELLM_RUST_DISABLE_ALL` | boolean | `false` | Disable all Rust acceleration |
| `LITELLM_RUST_FEATURE_CONFIG` | path | - | Path to JSON configuration file |
| `LITELLM_RUST_ALERT_FILE` | path | - | Path to alert log file |
| `RUST_LOG` | string | - | Rust logging level (debug, info, warn, error) |

### Feature-Specific Controls

Format: `LITELLM_RUST_{FEATURE_NAME}={value}`

**Values**:
- `true` / `enabled`: Enable feature (100% traffic)
- `false` / `disabled`: Disable feature
- `canary:{percentage}`: Canary deployment (e.g., `canary:10` for 10%)
- `rollout:{percentage}`: Gradual rollout (e.g., `rollout:50` for 50%)

**Available Features**:
```bash
# Core features
export LITELLM_RUST_RUST_ROUTING=true
export LITELLM_RUST_RUST_TOKEN_COUNTING=true
export LITELLM_RUST_RUST_RATE_LIMITING=rollout:75
export LITELLM_RUST_RUST_CONNECTION_POOLING=rollout:50

# Advanced features
export LITELLM_RUST_BATCH_TOKEN_COUNTING=canary:10
export LITELLM_RUST_ASYNC_ROUTING=canary:5
export LITELLM_RUST_PERFORMANCE_MONITORING=true
```

## JSON Configuration

### Configuration File Structure

```json
{
  "features": {
    "feature_name": {
      "state": "enabled|disabled|canary|gradual_rollout|shadow",
      "rollout_percentage": 100.0,
      "error_threshold": 5,
      "performance_threshold_ms": 100.0,
      "fallback_on_error": true,
      "dependencies": ["required_feature"]
    }
  },
  "global_settings": {
    "enable_automatic_degradation": true,
    "enable_performance_alerts": true,
    "metrics_retention_hours": 24,
    "alert_file": "/path/to/alerts.log"
  }
}
```

### Feature Configuration Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `state` | enum | `enabled` | Feature state (see Feature States) |
| `rollout_percentage` | float | `100.0` | Percentage of traffic (0-100) |
| `error_threshold` | int | `5` | Max errors before auto-disable |
| `performance_threshold_ms` | float | `1000.0` | Max latency before auto-disable |
| `fallback_on_error` | bool | `true` | Enable automatic fallback |
| `dependencies` | array | `[]` | Required features for this feature |

### Global Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_automatic_degradation` | bool | `true` | Enable error-based auto-disable |
| `enable_performance_alerts` | bool | `true` | Enable performance monitoring alerts |
| `metrics_retention_hours` | int | `24` | How long to keep metrics |
| `alert_file` | string | - | Path to write alerts |

## Component-Specific Configuration

### Token Counting

```bash
# Cache size for model encodings
export LITELLM_RUST_TOKEN_CACHE_SIZE=100

# Enable batch processing
export LITELLM_RUST_BATCH_TOKEN_COUNTING=canary:15
```

```json
{
  "features": {
    "rust_token_counting": {
      "state": "enabled",
      "error_threshold": 5,
      "performance_threshold_ms": 100.0
    },
    "batch_token_counting": {
      "state": "canary",
      "rollout_percentage": 15.0,
      "dependencies": ["rust_token_counting"]
    }
  }
}
```

### Advanced Routing

```bash
# Routing strategy
export LITELLM_RUST_ROUTING_STRATEGY=least_busy

# Async routing
export LITELLM_RUST_ASYNC_ROUTING=shadow:5
```

```json
{
  "features": {
    "rust_routing": {
      "state": "enabled",
      "error_threshold": 10,
      "performance_threshold_ms": 500.0
    },
    "async_routing": {
      "state": "shadow",
      "rollout_percentage": 5.0,
      "dependencies": ["rust_routing"]
    }
  }
}
```

### Rate Limiting

```bash
# Rate limiting configuration
export LITELLM_RUST_RUST_RATE_LIMITING=rollout:75
```

```json
{
  "features": {
    "rust_rate_limiting": {
      "state": "gradual_rollout",
      "rollout_percentage": 75.0,
      "error_threshold": 3,
      "performance_threshold_ms": 50.0
    }
  }
}
```

### Connection Pooling

```bash
# Connection pooling
export LITELLM_RUST_RUST_CONNECTION_POOLING=rollout:50
```

```json
{
  "features": {
    "rust_connection_pooling": {
      "state": "gradual_rollout",
      "rollout_percentage": 50.0,
      "error_threshold": 5,
      "performance_threshold_ms": 200.0
    }
  }
}
```

## Performance Monitoring Configuration

### Monitoring Settings

```bash
# Enable performance monitoring
export LITELLM_RUST_PERFORMANCE_MONITORING=true

# Alert configuration
export LITELLM_RUST_ALERT_FILE=/var/log/litellm_alerts.log
export LITELLM_RUST_METRICS_RETENTION_HOURS=48
```

```json
{
  "features": {
    "performance_monitoring": {
      "state": "enabled",
      "rollout_percentage": 100.0
    }
  },
  "global_settings": {
    "enable_performance_alerts": true,
    "metrics_retention_hours": 48,
    "alert_file": "/var/log/litellm_alerts.log"
  }
}
```

### Alert Thresholds

Default alert thresholds can be customized:

```json
{
  "alert_thresholds": {
    "rust_routing": {
      "latency_warning_ms": 300.0,
      "latency_critical_ms": 500.0,
      "error_rate_warning": 2.0,
      "error_rate_critical": 5.0
    },
    "rust_token_counting": {
      "latency_warning_ms": 50.0,
      "latency_critical_ms": 100.0,
      "error_rate_warning": 1.0,
      "error_rate_critical": 2.0
    }
  }
}
```

## Configuration Examples

### Development Environment

```bash
# Enable all features for development
export LITELLM_RUST_RUST_ROUTING=true
export LITELLM_RUST_RUST_TOKEN_COUNTING=true
export LITELLM_RUST_BATCH_TOKEN_COUNTING=true
export LITELLM_RUST_ASYNC_ROUTING=true
export LITELLM_RUST_PERFORMANCE_MONITORING=true
export RUST_LOG=debug
```

### Staging Environment

```json
{
  "features": {
    "rust_routing": {
      "state": "enabled",
      "error_threshold": 5,
      "performance_threshold_ms": 300.0
    },
    "rust_token_counting": {
      "state": "enabled",
      "error_threshold": 3,
      "performance_threshold_ms": 80.0
    },
    "batch_token_counting": {
      "state": "canary",
      "rollout_percentage": 50.0,
      "dependencies": ["rust_token_counting"]
    },
    "async_routing": {
      "state": "shadow",
      "rollout_percentage": 25.0,
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

### Production Environment

```json
{
  "features": {
    "rust_routing": {
      "state": "enabled",
      "error_threshold": 10,
      "performance_threshold_ms": 500.0,
      "fallback_on_error": true
    },
    "rust_token_counting": {
      "state": "enabled",
      "error_threshold": 5,
      "performance_threshold_ms": 100.0,
      "fallback_on_error": true
    },
    "rust_rate_limiting": {
      "state": "gradual_rollout",
      "rollout_percentage": 90.0,
      "error_threshold": 3,
      "performance_threshold_ms": 50.0,
      "fallback_on_error": true
    },
    "rust_connection_pooling": {
      "state": "gradual_rollout",
      "rollout_percentage": 75.0,
      "error_threshold": 5,
      "performance_threshold_ms": 200.0,
      "fallback_on_error": true
    },
    "batch_token_counting": {
      "state": "canary",
      "rollout_percentage": 10.0,
      "error_threshold": 2,
      "performance_threshold_ms": 80.0,
      "dependencies": ["rust_token_counting"],
      "fallback_on_error": true
    }
  },
  "global_settings": {
    "enable_automatic_degradation": true,
    "enable_performance_alerts": true,
    "metrics_retention_hours": 72,
    "alert_file": "/var/log/litellm_rust_alerts.log"
  }
}
```

## Configuration Validation

### Programmatic Validation

```python
import litellm_rust
import json

# Load and validate configuration
def validate_config(config_path):
    try:
        with open(config_path) as f:
            config = json.load(f)

        # Check required fields
        if 'features' not in config:
            raise ValueError("Missing 'features' section")

        # Validate feature configurations
        for feature, settings in config['features'].items():
            if 'state' not in settings:
                raise ValueError(f"Missing 'state' for feature {feature}")

            if settings.get('rollout_percentage', 0) > 100:
                raise ValueError(f"Invalid rollout_percentage for {feature}")

        print("Configuration valid")
        return True

    except Exception as e:
        print(f"Configuration error: {e}")
        return False

# Usage
validate_config('/path/to/config.json')
```

### Configuration Testing

```python
# Test configuration changes
def test_config_change(new_config):
    # Save current state
    original_status = litellm_rust.get_feature_status()

    try:
        # Apply new configuration
        os.environ['LITELLM_RUST_FEATURE_CONFIG'] = new_config

        # Reload configuration (restart required in practice)
        # Test functionality
        assert litellm_rust.is_enabled('rust_routing')

        # Check metrics
        stats = litellm_rust.get_performance_stats()
        assert len(stats) > 0

        print("Configuration test passed")

    except Exception as e:
        print(f"Configuration test failed: {e}")
        # Restore original configuration
        restore_config(original_status)
```

## Best Practices

### Configuration Management

1. **Version Control**: Store configurations in version control
2. **Environment Separation**: Use different configs per environment
3. **Gradual Changes**: Make incremental configuration changes
4. **Testing**: Test configuration changes in staging first
5. **Monitoring**: Monitor metrics after configuration changes

### Security

1. **File Permissions**: Restrict configuration file access
2. **Validation**: Validate all configuration inputs
3. **Audit Trail**: Log configuration changes
4. **Secrets**: Don't store secrets in configuration files

### Performance

1. **Cache Settings**: Tune cache sizes based on memory availability
2. **Thresholds**: Set appropriate error and performance thresholds
3. **Rollout Speed**: Don't rush production rollouts
4. **Monitoring**: Keep detailed metrics during rollouts

This configuration system provides flexible, safe control over Rust acceleration while maintaining production stability and observability.