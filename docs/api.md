# API Reference

Complete API documentation for Fast LiteLLM acceleration.

## Quick Start

```python
import fast_litellm  # Automatically accelerates LiteLLM on import
import litellm

# Check if Rust acceleration is available
if fast_litellm.RUST_ACCELERATION_AVAILABLE:
    print("Rust acceleration is active")

# All LiteLLM operations now use Rust acceleration where beneficial
response = litellm.completion(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Core Functions

### `apply_acceleration()`

Apply Rust acceleration with enhanced features. Called automatically on import.

```python
import fast_litellm
fast_litellm.apply_acceleration()
```

**Returns**: `bool` - True if acceleration was applied successfully

### `remove_acceleration()`

Remove Rust acceleration and restore Python implementations.

```python
fast_litellm.remove_acceleration()
```

### `health_check()`

Perform health check on all Rust components.

```python
health = fast_litellm.health_check()
print(f"Status: {health['status']}")
print(f"Rust available: {health['rust_available']}")
```

**Returns**: `Dict[str, Any]` - Health status for all components

## Feature Flag Management

### `is_enabled(feature_name, request_id=None)`

Check if a feature is enabled.

```python
enabled = fast_litellm.is_enabled("rust_routing", "request_123")
```

**Parameters**:
- `feature_name` (str): Name of the feature (`rust_routing`, `rust_token_counting`, `rust_rate_limiting`, `rust_connection_pooling`)
- `request_id` (str, optional): Request ID for consistent rollout

**Returns**: `bool` - True if feature is enabled

### `get_feature_status()`

Get comprehensive feature flag status.

```python
status = fast_litellm.get_feature_status()
```

**Returns**: `Dict[str, Any]` - Complete feature flag status

### `reset_errors(feature_name=None)`

Reset error counts for features (errors can trigger automatic feature disabling).

```python
fast_litellm.reset_errors("rust_routing")  # Reset specific feature
fast_litellm.reset_errors()                # Reset all features
```

## Performance Monitoring

### `record_performance(component, operation, duration_ms, success=True, input_size=None, output_size=None)`

Record a performance metric.

```python
fast_litellm.record_performance(
    component="rust_token_counting",
    operation="count_tokens",
    duration_ms=15.5,
    success=True,
    input_size=1024
)
```

**Parameters**:
- `component` (str): Component name
- `operation` (str): Operation name
- `duration_ms` (float): Duration in milliseconds
- `success` (bool): Whether operation was successful
- `input_size` (int, optional): Input size in bytes/tokens
- `output_size` (int, optional): Output size in bytes/tokens

### `get_performance_stats(component=None)`

Get performance statistics.

```python
# Get stats for specific component
stats = fast_litellm.get_performance_stats("rust_routing")

# Get stats for all components
all_stats = fast_litellm.get_performance_stats()
```

**Returns**: `Dict[str, Any]` - Performance statistics

### `compare_implementations(rust_component, python_component)`

Compare Rust vs Python implementation performance.

```python
comparison = fast_litellm.compare_implementations(
    "rust_routing",
    "python_routing"
)
```

**Returns**: `Dict[str, Any]` - Comparison metrics

### `get_recommendations()`

Get optimization recommendations based on collected metrics.

```python
recommendations = fast_litellm.get_recommendations()
for rec in recommendations:
    print(f"{rec['type']}: {rec['message']}")
```

**Returns**: `List[Dict[str, Any]]` - List of recommendations

### `export_performance_data(component=None, format="json")`

Export performance data.

```python
# Export as JSON
json_data = fast_litellm.export_performance_data(format="json")

# Export specific component
csv_data = fast_litellm.export_performance_data(
    component="rust_routing",
    format="csv"
)
```

**Parameters**:
- `component` (str, optional): Specific component to export
- `format` (str): Export format ("json" or "csv")

**Returns**: `str` - Exported data

## Rust Component APIs

When Rust acceleration is available, these classes are exposed via `fast_litellm._rust`:

### SimpleTokenCounter

Token counting with tiktoken-rs (model-specific encodings).

```python
from fast_litellm import _rust

counter = _rust.SimpleTokenCounter(model_max_tokens=4096)

# Count tokens in text
tokens = counter.count_tokens("Hello world", "gpt-4")

# Batch processing
texts = ["Text 1", "Text 2", "Text 3"]
token_counts = counter.count_tokens_batch(texts, "gpt-4")

# Estimate cost
cost = counter.estimate_cost(input_tokens=1000, output_tokens=500, model="gpt-4")

# Get model limits
limits = counter.get_model_limits("gpt-4")
```

### SimpleRateLimiter

Rate limiting with token bucket and sliding window algorithms.

```python
from fast_litellm import _rust

limiter = _rust.SimpleRateLimiter(requests_per_minute=60)

# Check if request is allowed
result = limiter.check("user_123")
if result["allowed"]:
    print(f"Remaining: {result['remaining_requests']}")
else:
    print(f"Retry after: {result.get('retry_after_ms')}ms")

# Simple boolean check
if limiter.is_allowed("user_123"):
    # Process request
    pass

# Get remaining requests
remaining = limiter.get_remaining("user_123")

# Get statistics
stats = limiter.get_stats()
```

### SimpleConnectionPool

Connection pool with health tracking and lifecycle management.

```python
from fast_litellm import _rust

pool = _rust.SimpleConnectionPool(pool_name="default")

# Get a connection
conn_id = pool.get_connection("https://api.openai.com")
if conn_id:
    try:
        # Use connection...
        pass
    finally:
        pool.return_connection(conn_id)

# Health check
is_healthy = pool.health_check(conn_id)

# Cleanup expired connections
pool.cleanup()

# Get statistics
stats = pool.get_stats()
```

### AdvancedRouter

Router with multiple strategies (simple_shuffle, least_busy, latency_based, cost_based).

```python
from fast_litellm import _rust

router = _rust.AdvancedRouter(strategy="simple_shuffle")

# Get an available deployment
model_list = [
    {"model_name": "gpt-4", "litellm_params": {"model": "gpt-4"}},
    {"model_name": "gpt-4", "litellm_params": {"model": "gpt-4-turbo"}},
]
deployment = router.get_available_deployment(
    model_list=model_list,
    model="gpt-4",
    blocked_models=[]
)
```

## Standalone Functions

These functions are available directly from `fast_litellm`:

```python
import fast_litellm

# Rate limiting
result = fast_litellm.check_rate_limit("user_key")
stats = fast_litellm.get_rate_limit_stats()

# Connection pool
conn_id = fast_litellm.get_connection("https://api.openai.com")
fast_litellm.return_connection(conn_id)
fast_litellm.remove_connection(conn_id)
is_healthy = fast_litellm.health_check_connection(conn_id)
fast_litellm.cleanup_expired_connections()
pool_stats = fast_litellm.get_connection_pool_stats()

# Routing
deployment = fast_litellm.get_available_deployment(
    model_list=model_list,
    model="gpt-4",
    blocked_models=[],
    context=None,
    settings=None
)

# Patch status
status = fast_litellm.get_patch_status()
```

## Constants

### `RUST_ACCELERATION_AVAILABLE`

Boolean indicating if Rust acceleration is available.

```python
if fast_litellm.RUST_ACCELERATION_AVAILABLE:
    print("Rust acceleration is available")
else:
    print("Using Python fallbacks")
```

### `__version__`

Package version string.

```python
print(f"Fast LiteLLM version: {fast_litellm.__version__}")
```

## Error Handling

All functions handle errors gracefully with automatic fallback:

- **ImportError**: Rust components not available, Python fallback used
- **RuntimeError**: Rust operation failed, automatic fallback to Python
- **ValueError**: Invalid parameters, exception raised with clear message

```python
import fast_litellm

# Safe usage pattern
if fast_litellm.RUST_ACCELERATION_AVAILABLE:
    # Use Rust-accelerated functions
    result = fast_litellm.check_rate_limit("key")
else:
    # Handle Python fallback
    print("Using Python fallbacks")
```

## Environment Variables

Configure behavior via environment variables:

```bash
# Disable specific features
export FAST_LITELLM_RUST_ROUTING=false
export FAST_LITELLM_RUST_TOKEN_COUNTING=false

# Enable canary rollout (10% of traffic)
export FAST_LITELLM_RUST_ROUTING=canary:10

# Custom configuration file
export FAST_LITELLM_FEATURE_CONFIG=/path/to/config.json
```

## Performance Tips

Based on benchmarks, here's when to use Rust acceleration:

| Use Case | Recommendation |
|----------|----------------|
| Connection pooling | ✅ Always use (3x faster) |
| Rate limiting | ✅ Always use (1.6x faster) |
| Large text tokenization | ✅ Use for texts >500 chars (1.5x faster) |
| High-cardinality rate limits | ✅ Use for 100+ unique keys (42x memory savings) |
| Small text tokenization | ⚠️ Python may be faster (FFI overhead) |
| Routing with Python objects | ⚠️ Python may be faster (conversion overhead) |
