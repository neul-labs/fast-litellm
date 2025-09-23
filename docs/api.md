# API Reference

Complete API documentation for LiteLLM Rust acceleration.

## Core Functions

### `apply_acceleration()`

Apply Rust acceleration with enhanced features.

```python
import litellm_rust
litellm_rust.apply_acceleration()
```

**Returns**: `bool` - True if acceleration was applied successfully

### `remove_acceleration()`

Remove Rust acceleration and restore Python implementations.

```python
litellm_rust.remove_acceleration()
```

### `health_check()`

Perform health check on all Rust components.

```python
health = litellm_rust.health_check()
print(f"Overall healthy: {health['overall_healthy']}")
```

**Returns**: `Dict[str, Any]` - Health status for all components

## Feature Flag Management

### `is_enabled(feature_name, request_id=None)`

Check if a feature is enabled.

```python
enabled = litellm_rust.is_enabled("rust_routing", "request_123")
```

**Parameters**:
- `feature_name` (str): Name of the feature
- `request_id` (str, optional): Request ID for consistent rollout

**Returns**: `bool` - True if feature is enabled

### `get_feature_status()`

Get comprehensive feature flag status.

```python
status = litellm_rust.get_feature_status()
```

**Returns**: `Dict[str, Any]` - Complete feature flag status

### `reset_errors(feature_name=None)`

Reset error counts for features.

```python
litellm_rust.reset_errors("rust_routing")  # Reset specific feature
litellm_rust.reset_errors()                # Reset all features
```

## Performance Monitoring

### `record_performance(component, operation, duration_ms, success=True, **kwargs)`

Record a performance metric.

```python
litellm_rust.record_performance(
    component="rust_token_counting",
    operation="count_tokens",
    duration_ms=15.5,
    success=True,
    input_size=1024,
    metadata={"model": "gpt-3.5-turbo"}
)
```

**Parameters**:
- `component` (str): Component name
- `operation` (str): Operation name
- `duration_ms` (float): Duration in milliseconds
- `success` (bool): Whether operation was successful
- `input_size` (int, optional): Input size in bytes/tokens
- `output_size` (int, optional): Output size in bytes/tokens
- `metadata` (dict, optional): Additional metadata

### `get_performance_stats(component=None)`

Get performance statistics.

```python
# Get stats for specific component
stats = litellm_rust.get_performance_stats("rust_routing")

# Get stats for all components
all_stats = litellm_rust.get_performance_stats()
```

**Returns**: `Dict[str, Any]` - Performance statistics

### `compare_implementations(rust_component, python_component)`

Compare Rust vs Python implementation performance.

```python
comparison = litellm_rust.compare_implementations(
    "rust_routing",
    "python_routing"
)
print(f"Speed improvement: {comparison['speed_improvement']['avg_latency']}x")
```

**Returns**: `Dict[str, Any]` - Comparison metrics

### `get_recommendations()`

Get optimization recommendations.

```python
recommendations = litellm_rust.get_recommendations()
for rec in recommendations:
    print(f"{rec['type']}: {rec['message']}")
```

**Returns**: `List[Dict[str, Any]]` - List of recommendations

### `export_performance_data(component=None, format="json")`

Export performance data.

```python
# Export as JSON
json_data = litellm_rust.export_performance_data(format="json")

# Export specific component as CSV
csv_data = litellm_rust.export_performance_data(
    component="rust_routing",
    format="csv"
)
```

**Parameters**:
- `component` (str, optional): Specific component to export
- `format` (str): Export format ("json" or "csv")

**Returns**: `str` - Exported data

## Advanced Functions

### `get_patch_status()`

Get the current status of all patches.

```python
status = litellm_rust.get_patch_status()
print(f"Total patches: {status['total_patches']}")
```

**Returns**: `Dict[str, Any]` - Patch status information

## Constants

### `RUST_ACCELERATION_AVAILABLE`

Boolean indicating if Rust acceleration is available.

```python
if litellm_rust.RUST_ACCELERATION_AVAILABLE:
    print("Rust acceleration is available")
```

## Rust Component APIs

When Rust acceleration is available, additional APIs are exposed:

### Token Counting

```python
from litellm_rust.rust_extensions import litellm_token

counter = litellm_token.SimpleTokenCounter(cache_size=100)

# Single text
tokens = counter.count_tokens("Hello world", "gpt-3.5-turbo")

# Batch processing
texts = ["Text 1", "Text 2", "Text 3"]
token_counts = counter.count_tokens_batch(texts, "gpt-3.5-turbo")
```

### Advanced Routing

```python
from litellm_rust.rust_extensions import litellm_core

config = litellm_core.RouterConfig(
    routing_strategy=litellm_core.RoutingStrategy.LeastBusy,
    cooldown_time_seconds=60,
    max_retries=3,
    timeout_seconds=30
)

router = litellm_core.AdvancedRouter(config)
```

### Rate Limiting

```python
from litellm_rust.rust_extensions import litellm_rate_limiter

limiter = litellm_rate_limiter.SimpleRateLimiter()
allowed = limiter.check_rate_limit("user_123", limit=100, window_seconds=60)
```

### Connection Pooling

```python
from litellm_rust.rust_extensions import litellm_connection_pool

pool = litellm_connection_pool.SimpleConnectionPool()
# Use for HTTP connection management
```

## Error Handling

All functions properly handle errors and provide fallback behavior:

- **ImportError**: Rust components not available, Python fallback used
- **RuntimeError**: Rust operation failed, automatic fallback to Python
- **ValueError**: Invalid parameters, exception raised with clear message

## Type Hints

The package includes comprehensive type hints for all public APIs:

```python
from typing import Dict, List, Optional, Any
import litellm_rust

# All functions have proper type annotations
stats: Dict[str, Any] = litellm_rust.get_performance_stats()
recommendations: List[Dict[str, Any]] = litellm_rust.get_recommendations()
```