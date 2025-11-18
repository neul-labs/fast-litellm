# Fast LiteLLM

[![PyPI](https://img.shields.io/pypi/v/fast-litellm.svg)](https://pypi.org/project/fast-litellm/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/fast-litellm.svg)](https://pypi.org/project/fast-litellm/)

High-performance Rust acceleration for [LiteLLM](https://github.com/BerriAI/litellm) - targeting 2-20x performance improvements for token counting, routing, rate limiting, and connection management.

## Why Fast LiteLLM?

Fast LiteLLM is a drop-in Rust acceleration layer for LiteLLM that provides targeted performance improvements where it matters most:

- **Modest improvements** in already well-optimized operations like token counting
- **~46% faster** rate limiting with async and concurrent primitives
- **~39% faster** connection management with improved pooling
- **Enhanced batch processing** capabilities
- **Lock-free data structures** for concurrent operations

Built with PyO3 and Rust, it seamlessly integrates with existing LiteLLM code with zero configuration required. Performance gains are most significant in complex operations where Rust's concurrency model provides advantages over Python's.

## Installation

```bash
pip install fast-litellm
```

## Quick Start

```python
import fast_litellm  # Automatically accelerates LiteLLM
import litellm

# All LiteLLM operations now use Rust acceleration where available
response = litellm.completion(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

That's it! Just import `fast_litellm` before `litellm` and acceleration is automatically applied.

## Architecture

The acceleration uses PyO3 to create Python extensions from Rust code:

```
┌─────────────────────────────────────────────────────────────┐
│ LiteLLM Python Package                                      │
├─────────────────────────────────────────────────────────────┤
│ fast_litellm (Python Integration Layer)                    │
│ ├── Enhanced Monkeypatching                                │
│ ├── Feature Flags & Gradual Rollout                        │
│ ├── Performance Monitoring                                 │
│ └── Automatic Fallback                                     │
├─────────────────────────────────────────────────────────────┤
│ Rust Acceleration Components (PyO3)                        │
│ ├── core               (Advanced Routing)                   │
│ ├── tokens             (Token Counting)                    │
│ ├── connection_pool    (Connection Management)             │
│ └── rate_limiter       (Rate Limiting)                     │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **Zero Configuration**: Works automatically on import
- **Production Safe**: Built-in feature flags, monitoring, and automatic fallback to Python
- **Performance Monitoring**: Real-time metrics and optimization recommendations
- **Gradual Rollout**: Support for canary deployments and percentage-based feature rollout
- **Thread Safe**: Lock-free data structures using DashMap for concurrent operations
- **Type Safe**: Full Python type hints and type stubs included

## Performance Benchmarks

| Component | Baseline | Optimized | Use Case |
|-----------|----------|-----------|----------|
| Token Counting | Well-optimized | **~0x** | Individual token counting (LiteLLM already optimized) |
| Batch Token Counting | Python implementation | **+9%** | Processing multiple texts at once |
| Request Routing | Python implementation | **+0.7%** | Load balancing, model selection |
| Rate Limiting | Python implementation | **+46%** | Request throttling, quota management |
| Connection Pooling | Python implementation | **+39%** | HTTP reuse, latency reduction |

**Note:** Our benchmarking revealed that LiteLLM's core token counting is already well-optimized, so performance gains are most significant in complex operations like rate limiting and connection pooling, where Rust's concurrent primitives provide meaningful improvements.

## Configuration

Fast LiteLLM works out of the box with zero configuration. For advanced use cases, you can configure behavior via environment variables:

```bash
# Disable specific features
export FAST_LITELLM_RUST_ROUTING=false

# Gradual rollout (10% of traffic)
export FAST_LITELLM_BATCH_TOKEN_COUNTING=canary:10

# Custom configuration file
export FAST_LITELLM_FEATURE_CONFIG=/path/to/config.json
```

See the [Configuration Guide](https://github.com/neul-labs/fast-litellm/blob/main/docs/configuration.md) for all options.

## Requirements

- Python 3.8 or higher
- LiteLLM

Rust is **not** required for installation - prebuilt wheels are available for all major platforms.

## Development

To contribute or build from source:

**Prerequisites:**
- Python 3.8+
- Rust toolchain (1.70+)
- [maturin](https://www.maturin.rs/) for building Python extensions

**Setup:**

```bash
git clone https://github.com/neul-labs/fast-litellm.git
cd fast-litellm

# Install maturin
pip install maturin

# Build and install in development mode
maturin develop

# Run unit tests
pip install pytest pytest-asyncio
pytest tests/
```

### Integration Testing

Fast LiteLLM includes comprehensive integration tests that run LiteLLM's test suite with acceleration enabled:

```bash
# Setup LiteLLM for testing
./scripts/setup_litellm.sh

# Run LiteLLM tests with acceleration
./scripts/run_litellm_tests.sh

# Compare performance (with vs without acceleration)
./scripts/compare_performance.py
```

This ensures Fast LiteLLM doesn't break any LiteLLM functionality. See the [Testing Guide](https://github.com/neul-labs/fast-litellm/blob/main/docs/testing.md) for details.

For more information, see our [Contributing Guide](https://github.com/neul-labs/fast-litellm/blob/main/docs/contributing.md).

## Documentation

- [Performance Analysis](https://github.com/neul-labs/fast-litellm/blob/main/docs/performance-analysis.md) - Realistic benchmarks and expectations
- [API Reference](https://github.com/neul-labs/fast-litellm/blob/main/docs/api.md)
- [Architecture Guide](https://github.com/neul-labs/fast-litellm/blob/main/docs/architecture.md)
- [Feature Flags](https://github.com/neul-labs/fast-litellm/blob/main/docs/feature-flags.md)
- [Performance Monitoring](https://github.com/neul-labs/fast-litellm/blob/main/docs/monitoring.md)

## How It Works

Fast LiteLLM uses PyO3 to create Python extensions from Rust code:

```
┌─────────────────────────────────────────────────────────────┐
│ LiteLLM Python Package                                      │
├─────────────────────────────────────────────────────────────┤
│ fast_litellm (Python Integration Layer)                    │
│ ├── Enhanced Monkeypatching                                │
│ ├── Feature Flags & Gradual Rollout                        │
│ ├── Performance Monitoring                                 │
│ └── Automatic Fallback                                     │
├─────────────────────────────────────────────────────────────┤
│ Rust Acceleration Components (PyO3)                        │
│ ├── core               (Advanced Routing)                   │
│ ├── tokens             (Token Counting)                    │
│ ├── connection_pool    (Connection Management)             │
│ └── rate_limiter       (Rate Limiting)                     │
└─────────────────────────────────────────────────────────────┘
```

When you import `fast_litellm`, it automatically patches LiteLLM's performance-critical functions with Rust implementations while maintaining full compatibility with the Python API.

**Note**: Performance gains vary significantly by operation. Core token counting shows minimal improvement as LiteLLM is already well-optimized for these operations. The most significant gains (40-50%) come from complex concurrent operations like rate limiting and connection pooling. See [Performance Analysis](docs/performance-analysis.md) for detailed benchmarks and realistic expectations.

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/neul-labs/fast-litellm/blob/main/docs/contributing.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **GitHub**: https://github.com/neul-labs/fast-litellm
- **PyPI**: https://pypi.org/project/fast-litellm/
- **Issues**: https://github.com/neul-labs/fast-litellm/issues
- **LiteLLM**: https://github.com/BerriAI/litellm
