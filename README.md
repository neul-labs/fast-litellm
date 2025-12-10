# Fast LiteLLM

[![CI](https://github.com/neul-labs/fast-litellm/actions/workflows/ci.yml/badge.svg)](https://github.com/neul-labs/fast-litellm/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/fast-litellm.svg)](https://pypi.org/project/fast-litellm/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/fast-litellm.svg)](https://pypi.org/project/fast-litellm/)

High-performance Rust acceleration for [LiteLLM](https://github.com/BerriAI/litellm) - providing significant performance improvements for connection pooling, rate limiting, and memory-intensive workloads.

## Why Fast LiteLLM?

Fast LiteLLM is a drop-in Rust acceleration layer for LiteLLM that provides targeted performance improvements where it matters most:

- **3.2x faster** connection pooling with DashMap lock-free data structures
- **1.6x faster** rate limiting with atomic operations
- **1.5-1.7x faster** token counting for large texts
- **42x more memory efficient** for high-cardinality rate limiting (1000+ unique keys)
- **Lock-free concurrent access** using DashMap for thread-safe operations

Built with PyO3 and Rust, it seamlessly integrates with existing LiteLLM code with zero configuration required. Performance gains are most significant in connection pooling, rate limiting, and memory-intensive workloads.

## Installation

```bash
# Using uv (recommended)
uv add fast-litellm

# Or using pip
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

Benchmarks comparing production-grade Python implementations (with thread-safety) vs Rust:

| Component | Speedup | Memory | Best For |
|-----------|---------|--------|----------|
| **Connection Pool** | **3.2x faster** | Same | HTTP connection management |
| **Rate Limiting** | **1.6x faster** | Same | Request throttling, quota management |
| **Large Text Tokenization** | **1.5-1.7x faster** | Same | Processing long documents |
| **High-Cardinality Rate Limits** | **1.2x faster** | **42x less memory** | Many unique API keys/users |
| Concurrent Connection Pool | **1.2x faster** | Same | Multi-threaded workloads |
| Small Text Tokenization | 0.5x (Python faster) | Same | Short messages (FFI overhead) |
| Routing | 0.4x (Python faster) | Same | Model selection (FFI overhead) |

### Key Insights

✅ **Use Rust acceleration for:**
- Connection pooling (3x+ speedup)
- Rate limiting (1.5x+ speedup)
- Large text token counting (1.5x+ speedup)
- High-cardinality workloads (40x+ memory savings)

⚠️ **Python may be faster for:**
- Small text token counting (FFI overhead dominates)
- Routing with complex Python objects

Run benchmarks yourself:
```bash
python scripts/run_benchmarks.py --iterations 200
```

See [BENCHMARK.md](BENCHMARK.md) for detailed results.

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

See the configuration section in [CLAUDE.md](CLAUDE.md) for more options.

## Compatibility

| Component | Supported Versions |
|-----------|-------------------|
| **Python** | 3.9, 3.10, 3.11, 3.12, 3.13 |
| **Platforms** | Linux (x86_64, aarch64), macOS (x86_64, ARM64), Windows (x86_64) |
| **LiteLLM** | Latest stable release |
| **PyO3** | 0.24+ |

Rust is **not** required for installation - prebuilt wheels are available for all major platforms.

For detailed compatibility information, see [COMPATIBILITY.md](COMPATIBILITY.md).

## Development

To contribute or build from source:

**Prerequisites:**
- Python 3.9+
- Rust toolchain (1.70+)
- [uv](https://docs.astral.sh/uv/) for package management (recommended)
- [maturin](https://www.maturin.rs/) for building Python extensions

**Setup:**

```bash
git clone https://github.com/neul-labs/fast-litellm.git
cd fast-litellm

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install maturin
uv add --dev maturin

# Build and install in development mode
uv run maturin develop

# Run unit tests
uv add --dev pytest pytest-asyncio
uv run pytest tests/
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

This ensures Fast LiteLLM doesn't break any LiteLLM functionality.

## Documentation

- [API Reference](docs/api.md) - Complete API documentation
- [Contributing Guide](docs/contributing.md) - Development setup and guidelines

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **GitHub**: https://github.com/neul-labs/fast-litellm
- **PyPI**: https://pypi.org/project/fast-litellm/
- **Issues**: https://github.com/neul-labs/fast-litellm/issues
- **LiteLLM**: https://github.com/BerriAI/litellm
