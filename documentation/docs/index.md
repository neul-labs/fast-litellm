# Fast LiteLLM

**High-performance Rust acceleration for LiteLLM**

Fast LiteLLM is a drop-in acceleration layer that provides significant performance improvements for [LiteLLM](https://github.com/BerriAI/litellm) operations. Built with Rust and PyO3, it seamlessly integrates with existing code with zero configuration required.

Created by **Dipankar Sarkar** ([me@dipankar.name](mailto:me@dipankar.name)) at [Neul Labs](https://www.neul.uk).

## Key Benefits

| Component | Speedup | Best For |
|-----------|---------|----------|
| **Connection Pool** | 3.2x faster | HTTP connection management |
| **Rate Limiting** | 1.6x faster | Request throttling, quota management |
| **Token Counting** | 1.5-1.7x faster | Processing long documents |
| **Memory Efficiency** | 42x less memory | High-cardinality rate limiting |

## Quick Start

```python
import fast_litellm  # Enable acceleration
import litellm

# All LiteLLM operations now use Rust acceleration
response = litellm.completion(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

That's it! Just import `fast_litellm` before `litellm` and acceleration is automatically applied.

## Features

- **Zero Configuration** - Works automatically on import
- **Production Safe** - Built-in feature flags, monitoring, and automatic fallback
- **Performance Monitoring** - Real-time metrics and optimization recommendations
- **Gradual Rollout** - Support for canary deployments and percentage-based rollout
- **Thread Safe** - Lock-free data structures using DashMap
- **Type Safe** - Full Python type hints included

## Installation

=== "uv (recommended)"

    ```bash
    uv add fast-litellm
    ```

=== "pip"

    ```bash
    pip install fast-litellm
    ```

## Architecture

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
│ ├── connection_pool    (Lock-free Connection Management)    │
│ ├── rate_limiter       (Atomic Rate Limiting)               │
│ ├── tokens             (Fast Token Counting)                │
│ └── core               (Advanced Routing)                   │
└─────────────────────────────────────────────────────────────┘
```

## Compatibility

| Component | Supported |
|-----------|-----------|
| **Python** | 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 |
| **Platforms** | Linux, macOS, Windows |
| **LiteLLM** | Latest stable release |

Rust is **not** required for installation - prebuilt wheels are available for all major platforms.

## Next Steps

- [Installation Guide](getting-started/installation.md) - Detailed installation instructions
- [Quick Start](getting-started/quickstart.md) - Get up and running in minutes
- [Features Overview](features/overview.md) - Learn about all accelerated components
- [API Reference](api/reference.md) - Complete API documentation
- [Neul Labs](https://www.neul.uk) - About the team building Fast LiteLLM
