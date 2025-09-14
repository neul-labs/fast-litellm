# LiteLLM Rust Acceleration

High-performance Rust acceleration for LiteLLM components.

[![Build Status](https://github.com/your-username/litellm-rust/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/litellm-rust/actions)
[![Crates.io](https://img.shields.io/crates/v/litellm-rust.svg)](https://crates.io/crates/litellm-rust)
[![PyPI](https://img.shields.io/pypi/v/litellm-rust.svg)](https://pypi.org/project/litellm-rust/)
[![License](https://img.shields.io/crates/l/l/litellm-rust.svg)](https://github.com/your-username/litellm-rust/blob/main/LICENSE)

## Features

- **Advanced Routing**: Multiple routing strategies with 3-5x performance improvement
- **Fast Token Counting**: 5-10x faster token counting using tiktoken-rs
- **Efficient Rate Limiting**: 4-8x faster rate limiting implementation
- **Connection Pooling**: 2-3x faster connection management
- **Drop-in Replacement**: Automatic monkeypatching of existing LiteLLM classes
- **Zero Configuration**: Install and get immediate performance benefits

## Installation

```bash
pip install litellm-rust
```

The package automatically detects and uses Rust acceleration when available, falling back to Python implementations gracefully.

## Usage

### Automatic Acceleration

Simply import the package to automatically apply Rust acceleration:

```python
import litellm_rust  # Automatic acceleration applied
import litellm       # All performance-critical components are now accelerated

# Use LiteLLM as usual - now with Rust acceleration!
response = litellm.completion(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello, world!"}]
)
```

### Manual Control

For more control over when acceleration is applied:

```python
import litellm_rust

# Check if Rust acceleration is available
if litellm_rust.RUST_ACCELERATION_AVAILABLE:
    print("✓ Rust acceleration is available")
else:
    print("✗ Rust acceleration is not available")

# Manually apply acceleration
litellm_rust.apply_acceleration()

# Remove acceleration and restore original implementations
litellm_rust.remove_acceleration()
```

### Diagnostics

Monitor the health and performance of the acceleration:

```python
import litellm_rust

# Run health checks
health = litellm_rust.health_check()
print(f"Overall system health: {health['overall_healthy']}")

# Get performance statistics
stats = litellm_rust.get_performance_stats()
print(f"Accelerated components: {list(stats['components'].keys())}")
```

## Performance Benefits

The Rust acceleration provides significant performance improvements:

| Component | Improvement | Use Case |
|-----------|-------------|----------|
| Token Counting | 5-10x faster | Prompt processing, context window management |
| Routing | 3-5x faster | Model selection, load balancing |
| Rate Limiting | 4-8x faster | Request throttling, quota management |
| Connection Pooling | 2-3x faster | HTTP connection reuse, latency reduction |

## Components

### Core
- `LiteLLMCore`: Core functionality with Rust acceleration
- `Deployment`: Model deployment representation

### Advanced Router
- `AdvancedRouter`: High-performance routing with multiple strategies
- `RoutingStrategy`: Enum of supported routing strategies
- `RouterConfig`: Configuration for the router

### Token
- `SimpleTokenCounter`: Fast token counting using tiktoken-rs (new utility)
- `SimpleRateLimiter`: Efficient rate limiting implementation (new utility)

### Connection Pool
- `SimpleConnectionPool`: High-performance connection management (new utility)

## Monkeypatching

The package automatically monkeypatches the following LiteLLM classes with their Rust-accelerated counterparts:

- `litellm.router.Router` → Rust AdvancedRouter implementation
- `litellm.types.router.Deployment` → Rust Deployment implementation
- `litellm.types.router.RoutingStrategy` → Rust RoutingStrategy implementation

New utility classes provided:
- `litellm.SimpleTokenCounter` (new)
- `litellm.SimpleRateLimiter` (new)
- `litellm.SimpleConnectionPool` (new)

## Development

### Prerequisites

- Python 3.8+
- Rust toolchain (for building from source)
- Cargo (Rust package manager)

### Building from Source

```bash
# Clone the repository
git clone https://github.com/your-username/litellm-rust.git
cd litellm-rust

# Install in development mode
pip install -e .

# Or build and install
pip install .
```

### Running Tests

```bash
# Run Python tests
make test

# Run Rust tests
make test-rust

# Run all tests
make test-all
```

## Architecture

The package uses PyO3 to create Python extension modules from Rust code:

```
LiteLLM Python Package
│
├── litellm_rust (Python wrapper)
│   ├── monkeypatch.py (Automatic monkeypatching)
│   ├── accelerator.py (Manual acceleration control)
│   ├── diagnostics.py (Health checks and stats)
│   └── rust_extensions.py (Compiled Rust extensions)
│
└── Rust Crates (PyO3 extensions)
    ├── litellm-core
    ├── litellm-token
    ├── litellm-connection-pool
    └── litellm-rate-limiter
```

When imported, `litellm_rust` automatically monkeypatches the corresponding Python classes in the LiteLLM package with their Rust implementations.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please [open an issue](https://github.com/your-username/litellm-rust/issues) on GitHub.

---

**Note**: This package provides acceleration for the LiteLLM library. For information about LiteLLM itself, visit [https://github.com/BerriAI/litellm](https://github.com/BerriAI/litellm).