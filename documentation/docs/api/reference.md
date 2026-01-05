# API Reference

Complete API reference for Fast LiteLLM, maintained by Dipankar Sarkar at Neul Labs (https://www.neul.uk, me@dipankar.name).

## Module: fast_litellm

The main module provides access to all accelerated functionality.

### Constants

#### RUST_ACCELERATION_AVAILABLE

```python
fast_litellm.RUST_ACCELERATION_AVAILABLE: bool
```

`True` if Rust acceleration is available, `False` if falling back to Python.

```python
import fast_litellm

if fast_litellm.RUST_ACCELERATION_AVAILABLE:
    print("Rust acceleration is active")
```

---

## Core Functions

### health_check

```python
fast_litellm.health_check() -> Dict[str, Any]
```

Perform a health check on the acceleration system.

**Returns:**
```python
{
    "status": "ok",
    "rust_available": True,
    "components": ["core", "tokens", "connection_pool", "rate_limiter"]
}
```

**Example:**
```python
health = fast_litellm.health_check()
print(f"Status: {health['status']}")
```

---

### apply_acceleration

```python
fast_litellm.apply_acceleration() -> bool
```

Manually apply acceleration patches. Called automatically on import.

**Returns:** `True` if patches were applied successfully.

---

### remove_acceleration

```python
fast_litellm.remove_acceleration() -> None
```

Remove acceleration patches and restore original implementations.

---

### get_patch_status

```python
fast_litellm.get_patch_status() -> Dict[str, Any]
```

Get the current status of acceleration patches.

**Returns:**
```python
{
    "applied": True,
    "components": ["routing", "token_counting", "rate_limiting", "connection_pooling"]
}
```

---

## Feature Flags

### is_enabled

```python
fast_litellm.is_enabled(
    feature_name: str,
    request_id: Optional[str] = None
) -> bool
```

Check if a feature is enabled.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `feature_name` | str | Name of the feature to check |
| `request_id` | str (optional) | Request ID for gradual rollout |

**Example:**
```python
if fast_litellm.is_enabled("rust_routing"):
    # Use Rust routing
    pass
```

---

### get_feature_status

```python
fast_litellm.get_feature_status() -> Dict[str, Dict[str, Any]]
```

Get status of all features.

**Returns:**
```python
{
    "rust_routing": {"enabled": True, "errors": 0, "rollout_percentage": 100},
    "rust_token_counting": {"enabled": True, "errors": 0, "rollout_percentage": 100},
    "rust_rate_limiting": {"enabled": True, "errors": 0, "rollout_percentage": 100},
    "rust_connection_pool": {"enabled": True, "errors": 0, "rollout_percentage": 100}
}
```

---

### reset_errors

```python
fast_litellm.reset_errors(feature_name: Optional[str] = None) -> None
```

Reset error counts for features.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `feature_name` | str (optional) | Reset specific feature, or all if None |

---

## Performance Monitoring

### record_performance

```python
fast_litellm.record_performance(
    component: str,
    operation: str,
    duration_ms: float,
    success: Optional[bool] = True,
    input_size: Optional[int] = None,
    output_size: Optional[int] = None
) -> None
```

Record a performance metric.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `component` | str | Component name (e.g., "rate_limiter") |
| `operation` | str | Operation name (e.g., "check") |
| `duration_ms` | float | Duration in milliseconds |
| `success` | bool | Whether the operation succeeded |
| `input_size` | int | Optional input size in bytes |
| `output_size` | int | Optional output size in bytes |

---

### get_performance_stats

```python
fast_litellm.get_performance_stats(
    component: Optional[str] = None
) -> Dict[str, Any]
```

Get performance statistics.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `component` | str (optional) | Filter by component |

**Returns:** Dictionary of performance metrics.

---

### compare_implementations

```python
fast_litellm.compare_implementations(
    rust_component: str,
    python_component: str
) -> Dict[str, Any]
```

Compare Rust and Python implementation performance.

**Returns:**
```python
{
    "rust_avg_ms": 0.5,
    "python_avg_ms": 1.2,
    "speedup": 2.4,
    "recommendation": "use_rust"
}
```

---

### get_recommendations

```python
fast_litellm.get_recommendations() -> List[Dict[str, Any]]
```

Get optimization recommendations based on collected metrics.

**Returns:** List of recommendation dictionaries.

---

### export_performance_data

```python
fast_litellm.export_performance_data(
    component: Optional[str] = None,
    format: Optional[str] = "json"
) -> str
```

Export performance data.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `component` | str (optional) | Filter by component |
| `format` | str | Output format ("json" or "csv") |

**Returns:** Formatted performance data string.

---

## Rate Limiting

### check_rate_limit

```python
fast_litellm.check_rate_limit(key: str) -> Dict[str, Any]
```

Check if a request is allowed under rate limits.

**Returns:**
```python
{
    "allowed": True,
    "reason": "ok",
    "remaining_requests": 59,
    "retry_after_ms": None  # Only present if not allowed
}
```

---

### get_rate_limit_stats

```python
fast_litellm.get_rate_limit_stats() -> Dict[str, Any]
```

Get rate limiter statistics.

---

## Connection Pool

### get_connection

```python
fast_litellm.get_connection(endpoint: str) -> Optional[str]
```

Get a connection ID for an endpoint.

**Returns:** Connection ID string or None.

---

### return_connection

```python
fast_litellm.return_connection(connection_id: str) -> None
```

Return a connection to the pool.

---

### remove_connection

```python
fast_litellm.remove_connection(connection_id: str) -> None
```

Remove a connection from the pool.

---

### health_check_connection

```python
fast_litellm.health_check_connection(connection_id: str) -> bool
```

Check if a connection is healthy.

---

### cleanup_expired_connections

```python
fast_litellm.cleanup_expired_connections() -> None
```

Clean up expired/idle connections.

---

### get_connection_pool_stats

```python
fast_litellm.get_connection_pool_stats() -> Dict[str, Any]
```

Get connection pool statistics.

---

## Routing

### get_available_deployment

```python
fast_litellm.get_available_deployment(
    model_list: List[Dict],
    model: str,
    blocked_models: Optional[List[str]] = None,
    context: Optional[Any] = None,
    settings: Optional[Any] = None
) -> Optional[Dict]
```

Get an available deployment for a model.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `model_list` | List[Dict] | List of deployment configurations |
| `model` | str | Model name to route to |
| `blocked_models` | List[str] | Models to exclude |
| `context` | Any | Optional request context |
| `settings` | Any | Optional settings |

**Returns:** Deployment dictionary or None.

---

## Classes

### SimpleTokenCounter

Token counting with cost estimation.

```python
class SimpleTokenCounter:
    def __init__(self, model_max_tokens: int = 4096) -> None: ...
    def count_tokens(self, text: str, model: Optional[str] = None) -> int: ...
    def count_tokens_batch(self, texts: List[str], model: Optional[str] = None) -> List[int]: ...
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float: ...
    def get_model_limits(self, model: str) -> Dict[str, Any]: ...
    def validate_input(self, text: str, model: str) -> bool: ...
    @property
    def model_max_tokens(self) -> int: ...
```

---

### SimpleRateLimiter

Rate limiting with token bucket algorithm.

```python
class SimpleRateLimiter:
    def __init__(self, requests_per_minute: int = 60) -> None: ...
    def check(self, key: Optional[str] = None) -> Dict[str, Any]: ...
    def is_allowed(self, key: Optional[str] = None) -> bool: ...
    def get_remaining(self, key: Optional[str] = None) -> int: ...
    def get_stats(self) -> Dict[str, Any]: ...
```

---

### SimpleConnectionPool

Connection pool management.

```python
class SimpleConnectionPool:
    def __init__(self, pool_name: str = "default") -> None: ...
    def get_connection(self, endpoint: str) -> Optional[str]: ...
    def return_connection(self, connection_id: str) -> None: ...
    def health_check(self, connection_id: str) -> bool: ...
    def cleanup(self) -> None: ...
    def get_stats(self) -> Dict[str, Any]: ...
```

---

### AdvancedRouter

Advanced routing with multiple strategies.

```python
class AdvancedRouter:
    def __init__(self, strategy: str = "simple_shuffle") -> None: ...
    def get_available_deployment(
        self,
        model_list: List[Dict],
        model: str,
        blocked_models: Optional[List[str]] = None
    ) -> Optional[Dict]: ...
    @property
    def strategy(self) -> str: ...
```

**Strategies:**

- `simple_shuffle` - Random selection
- `least_busy` - Lowest active requests
- `latency_based` - Lowest average latency
- `cost_based` - Most cost-effective

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FAST_LITELLM_ENABLED` | `true` | Enable/disable all acceleration |
| `FAST_LITELLM_RUST_ROUTING` | `true` | Enable Rust routing |
| `FAST_LITELLM_RUST_TOKEN_COUNTING` | `true` | Enable Rust token counting |
| `FAST_LITELLM_RUST_RATE_LIMITING` | `true` | Enable Rust rate limiting |
| `FAST_LITELLM_RUST_CONNECTION_POOL` | `true` | Enable Rust connection pool |
| `FAST_LITELLM_FEATURE_CONFIG` | - | Path to feature config file |
| `FAST_LITELLM_BATCH_TOKEN_COUNTING` | `true` | Enable batch token counting |
