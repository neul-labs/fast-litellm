# Architecture

## Overview

The LiteLLM Rust Acceleration project uses PyO3 to create Python extension modules from Rust code. The architecture consists of several Rust crates that provide high-performance implementations of performance-critical LiteLLM components.

## Components

### Rust Crates

1. **`litellm-core`**: Core functionality and advanced router implementation
2. **`litellm-token`**: Token counting and rate limiting utilities
3. **`litellm-connection-pool`**: Connection pooling implementation
4. **`litellm-rate-limiter`**: Rate limiting implementation

### Python Package

The Python package (`litellm_rust`) provides a wrapper around the compiled Rust extensions with automatic monkeypatching capabilities.

## Data Flow

```
Python Application
       ↓
litellm_rust (Python wrapper)
       ↓
Automatic Monkeypatching
       ↓
Rust Extensions (via PyO3)
       ↓
LiteLLM Python Classes (accelerated)
```

## Performance Optimizations

The Rust implementations provide significant performance improvements through:

1. **Zero-copy data structures**: Minimizing memory allocations
2. **Lock-free concurrency**: Using atomic operations where possible
3. **Efficient algorithms**: Optimized routing and token counting algorithms
4. **Memory pooling**: Reusing allocated memory buffers