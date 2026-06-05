# Architecture

Fast LiteLLM is a drop-in Rust acceleration layer for LiteLLM. It sits between the Python LiteLLM package and your application, replacing hot-path implementations with Rust equivalents while leaving the rest of LiteLLM untouched.

## Layered View

```
┌─────────────────────────────────────────────────────────────┐
│ LiteLLM Python Package                                      │
├─────────────────────────────────────────────────────────────┤
│ fast_litellm (Python Integration Layer)                     │
│ ├── Enhanced Monkeypatching                                 │
│ ├── Feature Flags & Gradual Rollout                         │
│ ├── Performance Monitoring                                  │
│ └── Automatic Fallback                                      │
├─────────────────────────────────────────────────────────────┤
│ Rust Acceleration Components (PyO3)                         │
│ ├── core               (Advanced Routing)                   │
│ ├── tokens             (Token Counting)                     │
│ ├── connection_pool    (Connection Management)              │
│ └── rate_limiter       (Rate Limiting)                      │
└─────────────────────────────────────────────────────────────┘
```

## Repository Layout

| Path | Purpose |
|------|---------|
| `src/lib.rs` | PyO3 module entry point; registers all `#[pyfunction]` and `#[pyclass]` exports |
| `src/connection_pool.rs` | Lock-free connection pool backed by DashMap |
| `src/rate_limiter.rs` | Token-bucket and sliding-window rate limiter |
| `src/tokens.rs` | tiktoken-rs-based token counting and cost estimation |
| `src/core.rs` | Routing strategies |
| `src/feature_flags.rs` | Feature gate evaluation and error tracking |
| `src/performance_monitor.rs` | Metrics collection and recommendation logic |
| `src/pricing.rs` | Model pricing data for cost estimation |
| `fast_litellm/__init__.py` | Python package; imports the `_rust` extension and wires fallbacks |
| `fast_litellm/enhanced_monkeypatch.py` | Applies patches to LiteLLM at import time |
| `fast_litellm/feature_flags.py` | Pure-Python feature flag implementation (fallback) |
| `fast_litellm/performance_monitor.py` | Pure-Python performance monitor (fallback) |
| `fast_litellm/diagnostics.py` | Pure-Python health check (fallback) |
| `fast_litellm/__init__.pyi` | Type stubs for the public API |

## Import-Time Flow

The package executes the following on `import fast_litellm` (see `fast_litellm/__init__.py`):

1. Try to `from ._rust import *` — the compiled PyO3 extension.
2. If the import succeeds, set `RUST_ACCELERATION_AVAILABLE = True` and call `enhanced_monkeypatch.enhanced_apply_acceleration(...)` to install patches on LiteLLM.
3. If the Rust import fails, emit an `ImportWarning`, set `RUST_ACCELERATION_AVAILABLE = False`, and bind the public API names to pure-Python fallbacks from `fast_litellm.diagnostics`, `fast_litellm.feature_flags`, and `fast_litellm.performance_monitor`.
4. Catch `TypeError` from the patching step silently — this covers LiteLLM versions that use Python 3.10+ syntax on Python 3.9.

The net effect is that `import fast_litellm` is safe even when the Rust extension or LiteLLM itself is missing or incompatible: the public API is always populated, just with different backends.

## Rust Components

All Rust components are exposed via PyO3. The module entry point is:

```rust
#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // classes: SimpleTokenCounter, SimpleRateLimiter,
    //          SimpleConnectionPool, AdvancedRouter
    // functions: health_check, apply_acceleration, ...
}
```

### Connection Pool

Backed by [`dashmap::DashMap`](https://docs.rs/dashmap), a concurrent hash map providing:

- Lock-free reads (multiple threads read simultaneously)
- Fine-grained per-bucket write locking
- Atomic operations without a single global lock

Public surface: `SimpleConnectionPool` class plus the `get_connection`, `return_connection`, `remove_connection`, `health_check_connection`, `cleanup_expired_connections`, and `get_connection_pool_stats` standalone functions.

### Rate Limiter

Combines a token-bucket algorithm with sliding-window counters, using `std::sync::atomic` primitives for lock-free updates. The `SimpleRateLimiter` constructor takes `requests_per_minute` and derives `requests_per_second`, `requests_per_hour`, and `burst_size = max(rpm / 10, 5)` (see `src/lib.rs`).

### Token Counting

Uses [`tiktoken-rs`](https://crates.io/crates/tiktoken-rs) with model-specific BPE encodings (`cl100k_base`, `o200k_base`, `p50k_base`, `r50k_base`). Encodings are cached so initialization cost is paid once per model.

### Router

`AdvancedRouter` exposes four strategies (`simple_shuffle`, `least_busy`, `latency_based`, `cost_based`) and supports a `blocked_models` filter. Metrics for least-busy and latency-based routing are tracked in a DashMap keyed by deployment.

## Python Integration Layer

### Enhanced Monkeypatching

`fast_litellm/enhanced_monkeypatch.py` performs the patching on LiteLLM's module objects. The functions exposed to users are:

- `apply_acceleration()` — manually re-apply patches
- `remove_acceleration()` — restore original LiteLLM implementations
- `get_patch_status()` — report which components are patched

### Feature Flags

Per-feature gates evaluated on every call. Each flag supports three forms via environment variables:

```bash
export FAST_LITELLM_RUST_ROUTING=true        # enabled
export FAST_LITELLM_RUST_ROUTING=false       # disabled
export FAST_LITELLM_RUST_ROUTING=canary:10   # 10% of traffic
export FAST_LITELLM_RUST_ROUTING=rollout:50  # 50% of traffic
```

Errors are counted per feature; when a threshold is exceeded the feature auto-disables (circuit breaker). Reset with `fast_litellm.reset_errors()`.

### Performance Monitor

Records duration, input/output size, and success per operation. The `compare_implementations(rust_component, python_component)` function returns a comparison dict with `rust_avg_ms`, `python_avg_ms`, `speedup`, and a recommendation, which `get_recommendations()` aggregates into actionable advice.

## Build & Distribution

| Tool | Role |
|------|------|
| `maturin` | Builds the PyO3 extension and packages wheels |
| `pyo3` 0.24 | Python/Rust FFI |
| `cargo` | Rust dependency resolution and release profile (`lto = true`, `codegen-units = 1`, `strip = true`) |

Prebuilt wheels are published for Linux (x86_64, aarch64), macOS (x86_64, ARM64), and Windows (x86_64) across Python 3.8–3.13. Rust is **not** required to install from PyPI.

## See Also

- [Features Overview](../features/overview.md)
- [API Reference](../api/reference.md)
- [Contributing](contributing.md)
