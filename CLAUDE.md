# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LiteLLM Rust is a high-performance Rust acceleration layer for LiteLLM that provides drop-in replacements for performance-critical components. It uses PyO3 to create Python extensions from Rust code, achieving 2-20x performance improvements while maintaining full compatibility with the existing Python API.

## Build Commands

### Initial Setup
```bash
# Install maturin (Rust-Python build tool)
pip install maturin

# Development build (creates editable install)
maturin develop

# Or use the automated setup script
./scripts/setup_dev.sh
```

### Building
```bash
# Development build (fast, with debug symbols)
maturin develop

# Release build (optimized)
maturin build --release

# Build wheel for distribution
maturin build --release --out dist

# Build for specific Python version
maturin build --interpreter python3.11
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_accelerator.py

# Run single test
pytest tests/test_basic.py::test_import_package

# Run tests with coverage
pytest tests/ --cov=litellm_rust --cov-report=html

# Run tests excluding slow benchmarks
pytest tests/ -m "not slow"

# Run only integration tests
pytest tests/ -m integration

# Run Rust tests
cargo test

# Run Rust tests with specific module
cargo test --lib core
```

### Code Quality
```bash
# Python formatting
black litellm_rust/ tests/

# Python import sorting
isort litellm_rust/ tests/

# Python linting
flake8 litellm_rust/
mypy litellm_rust/
ruff check litellm_rust/

# Rust formatting
cargo fmt

# Rust linting
cargo clippy -- -D warnings

# Run all quality checks
black --check . && isort --check-only . && flake8 . && mypy litellm_rust/ && cargo fmt -- --check && cargo clippy
```

## Architecture

### Dual-Layer Design

The project has two interconnected layers:

1. **Rust Layer (`src/`)**: High-performance implementations using PyO3
   - `lib.rs`: Main PyO3 module that exports Python functions
   - `core.rs`: Advanced routing with DashMap for lock-free concurrency
   - `tokens.rs`: Token counting (placeholder for tiktoken-rs integration)
   - `connection_pool.rs`: Connection management with atomic operations
   - `rate_limiter.rs`: Token bucket and sliding window rate limiting
   - `feature_flags.rs`: Gradual rollout and canary deployment system
   - `performance_monitor.rs`: Real-time metrics collection

2. **Python Layer (`litellm_rust/`)**: Integration and fallback logic
   - `__init__.py`: Package entry with automatic Rust import and fallback
   - `enhanced_monkeypatch.py`: Smart patching with performance monitoring
   - `feature_flags.py`: Python-side feature flag management
   - `performance_monitor.py`: Performance tracking and comparison
   - Falls back to Python implementations if Rust extensions unavailable

### Monkeypatching Strategy

The system uses enhanced monkeypatching to replace LiteLLM components:

1. Import detection: When `litellm_rust` is imported, it automatically attempts to load Rust extensions
2. Smart replacement: `PerformanceWrapper` class wraps functions with:
   - Feature flag checking (per-request rollout control)
   - Performance monitoring (timing and metrics)
   - Automatic fallback on errors
3. Gradual rollout: Feature flags control which requests use Rust vs Python

### Key Design Patterns

1. **Lock-Free Concurrency**: Uses DashMap instead of standard HashMap for thread-safe operations without locks
2. **Atomic Operations**: Rate limiters and connection pools use atomic integers for concurrent access
3. **Zero-Copy Returns**: PyO3 conversions minimize data copying between Rust and Python
4. **Feature Flags**: Every Rust component can be individually enabled/disabled with percentage-based rollout

## Critical Files

### Build Configuration
- `pyproject.toml`: Main package configuration with maturin settings
- `Cargo.toml`: Rust package configuration with PyO3 dependencies
- `[tool.maturin]` section: Configures module name as `litellm_rust._rust`

### Entry Points
- `litellm_rust/__init__.py`: Main package entry, imports from `._rust` module
- `src/lib.rs`: Rust entry point with `#[pymodule]` definition

### Integration Points
- The Rust module is compiled as `_rust.so` and imported as `litellm_rust._rust`
- All Rust functions are exposed via `#[pyfunction]` decorators
- JSON data is converted between `serde_json::Value` and Python objects

## Development Workflow

### Adding New Rust Functionality

1. Add Rust implementation in appropriate `src/*.rs` file
2. Export function in `src/lib.rs` with `#[pyfunction]` decorator
3. Add to module in `lib.rs` `#[pymodule]` function
4. Rebuild with `maturin develop`
5. Add Python wrapper in `litellm_rust/` if needed
6. Add tests in `tests/`

### Testing Cycle

1. Make changes to Rust code
2. Run `maturin develop` to rebuild
3. Run `pytest tests/test_specific.py -v` to test
4. Use `pytest tests/ -k "test_name"` for specific test

### Performance Testing

```bash
# Run benchmarks
pytest tests/benchmark_*.py

# Compare Rust vs Python implementations
python examples/benchmark.py

# Profile specific operations
pytest tests/test_performance_comparison.py -v
```

## Important Context

### LiteLLM Integration
- This package monkeypatches the actual LiteLLM library (at `~/Github/litellm`)
- The goal is seamless acceleration without code changes in user applications
- Import order matters: `import litellm_rust` must come before `import litellm`

### Feature Flag System
- Configuration via `litellm_rust/feature_flags.json`
- Environment variable overrides: `LITELLM_RUST_ENABLED=true`
- Per-feature control: `rust_routing`, `rust_token_counting`, `rust_rate_limiting`, `rust_connection_pool`
- Gradual rollout percentages and canary deployments supported

### Performance Monitoring
- Automatic performance comparison between Rust and Python implementations
- Metrics stored in-memory with DashMap
- Recommendations generated based on performance data
- Export via `get_performance_stats()` and `export_performance_data()`

### Error Handling
- All Rust functions have automatic Python fallback
- Errors are tracked per feature with automatic circuit breaking
- After 10 errors (default), feature auto-disables
- Reset with `reset_errors()` function

## Common Issues and Solutions

### Build Issues
- If `maturin develop` fails, ensure Rust toolchain is installed: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- For "module not found" errors, check that maturin built to the correct Python environment
- Use `maturin build --interpreter $(which python)` for specific Python version

### Import Issues
- The Rust module is named `_rust`, not `rust_extensions`
- If import fails, check `target/wheels/` for the built wheel
- Verify with: `python -c "import litellm_rust._rust"`

### Performance Testing
- Benchmarks require the actual LiteLLM library to be installed
- Some tests are marked as `slow` and skipped by default
- Use `pytest -m slow` to run comprehensive benchmarks