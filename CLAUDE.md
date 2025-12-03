# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fast LiteLLM is a high-performance Rust acceleration layer for LiteLLM that provides drop-in replacements for performance-critical components. It uses PyO3 to create Python extensions from Rust code, achieving 2-20x performance improvements while maintaining full compatibility with the existing Python API.

## Build Commands

### Initial Setup
```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install maturin and development dependencies
uv add --dev maturin

# Development build (creates editable install)
uv run maturin develop

# Or use the automated setup script
./scripts/setup_dev.sh
```

### Building
```bash
# Development build (fast, with debug symbols)
uv run maturin develop

# Release build (optimized)
uv run maturin build --release

# Build wheel for distribution
uv run maturin build --release --out dist

# Build for specific Python version
uv run maturin build --interpreter python3.11
```

### Testing
```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_accelerator.py

# Run single test
uv run pytest tests/test_basic.py::test_import_package

# Run tests with coverage
uv run pytest tests/ --cov=fast_litellm --cov-report=html

# Run tests excluding slow benchmarks
uv run pytest tests/ -m "not slow"

# Run only integration tests
uv run pytest tests/ -m integration

# Run Rust tests
cargo test

# Run Rust tests with specific module
cargo test --lib core
```

### Code Quality
```bash
# Python formatting
uv run black fast_litellm/ tests/

# Python import sorting
uv run isort fast_litellm/ tests/

# Python linting
uv run flake8 fast_litellm/
uv run mypy fast_litellm/
uv run ruff check fast_litellm/

# Rust formatting
cargo fmt

# Rust linting
cargo clippy -- -D warnings

# Run all quality checks
uv run black --check . && uv run isort --check-only . && uv run flake8 . && uv run mypy fast_litellm/ && cargo fmt -- --check && cargo clippy
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

2. **Python Layer (`fast_litellm/`)**: Integration and fallback logic
   - `__init__.py`: Package entry with automatic Rust import and fallback
   - `enhanced_monkeypatch.py`: Smart patching with performance monitoring
   - `feature_flags.py`: Python-side feature flag management
   - `performance_monitor.py`: Performance tracking and comparison
   - Falls back to Python implementations if Rust extensions unavailable

### Monkeypatching Strategy

The system uses enhanced monkeypatching to replace LiteLLM components:

1. Import detection: When `fast_litellm` is imported, it automatically attempts to load Rust extensions
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
- `[tool.maturin]` section: Configures module name as `fast_litellm._rust`

### Entry Points
- `fast_litellm/__init__.py`: Main package entry, imports from `._rust` module
- `src/lib.rs`: Rust entry point with `#[pymodule]` definition

### Integration Points
- The Rust module is compiled as `_rust.so` and imported as `fast_litellm._rust`
- All Rust functions are exposed via `#[pyfunction]` decorators
- JSON data is converted between `serde_json::Value` and Python objects

## Development Workflow

### Adding New Rust Functionality

1. Add Rust implementation in appropriate `src/*.rs` file
2. Export function in `src/lib.rs` with `#[pyfunction]` decorator
3. Add to module in `lib.rs` `#[pymodule]` function
4. Rebuild with `uv run maturin develop`
5. Add Python wrapper in `fast_litellm/` if needed
6. Add tests in `tests/`

### Testing Cycle

1. Make changes to Rust code
2. Run `uv run maturin develop` to rebuild
3. Run `uv run pytest tests/test_specific.py -v` to test
4. Use `uv run pytest tests/ -k "test_name"` for specific test

### Integration Testing with LiteLLM

Fast LiteLLM includes scripts to test against the actual LiteLLM library:

```bash
# Setup LiteLLM for integration testing
./scripts/setup_litellm.sh

# Run LiteLLM's tests with Fast LiteLLM acceleration
./scripts/run_litellm_tests.sh

# Run specific LiteLLM test file
./scripts/run_litellm_tests.sh tests/test_completion.py

# Compare performance with and without acceleration
./scripts/compare_performance.py tests/test_completion.py
```

This ensures that Fast LiteLLM doesn't break any LiteLLM functionality. The scripts:
1. Clone LiteLLM to `.litellm/` directory
2. Apply Fast LiteLLM acceleration via monkeypatching
3. Run LiteLLM's test suite
4. Report results and performance metrics

### Performance Testing

```bash
# Run benchmarks
uv run pytest tests/benchmark_*.py

# Compare Rust vs Python implementations
uv run python examples/benchmark.py

# Profile specific operations
uv run pytest tests/test_performance_comparison.py -v

# Full performance comparison with LiteLLM
./scripts/compare_performance.py
```

## Important Context

### LiteLLM Integration
- This package monkeypatches the actual LiteLLM library (at `~/Github/litellm`)
- The goal is seamless acceleration without code changes in user applications
- Import order matters: `import fast_litellm` must come before `import litellm`

### Feature Flag System
- Configuration via `fast_litellm/feature_flags.json`
- Environment variable overrides: `FAST_LITELLM_ENABLED=true`
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
- Use `uv run maturin build --interpreter $(which python)` for specific Python version

### Import Issues
- The Rust module is named `_rust`, not `rust_extensions`
- If import fails, check `target/wheels/` for the built wheel
- Verify with: `uv run python -c "import fast_litellm._rust"`

### Performance Testing
- Benchmarks require the actual LiteLLM library to be installed
- Some tests are marked as `slow` and skipped by default
- Use `uv run pytest -m slow` to run comprehensive benchmarks
