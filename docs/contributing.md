# Contributing to Fast LiteLLM

Thank you for your interest in contributing!

## Development Setup

### Prerequisites

- Python 3.9+ (3.12 recommended)
- Rust toolchain 1.70+ (`rustup` recommended)
- [uv](https://docs.astral.sh/uv/) for package management
- Git

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/neul-labs/fast-litellm.git
cd fast-litellm

# Run the setup script (installs uv if needed)
./scripts/setup_dev.sh
```

### Manual Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync --all-extras

# Build Rust extensions (release build for performance)
uv run maturin develop --release
```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make changes and rebuild:
   ```bash
   # Rebuild after Rust changes
   uv run maturin develop --release
   ```

3. Run tests:
   ```bash
   # Python tests
   uv run pytest tests/ -v

   # Rust tests
   cargo test
   ```

4. Format and lint:
   ```bash
   # Python
   uv run black fast_litellm/ tests/
   uv run isort fast_litellm/ tests/

   # Rust
   cargo fmt
   cargo clippy
   ```

5. Commit using conventional commits:
   ```bash
   git commit -m "feat: add your feature"
   ```

## Coding Standards

### Rust
- Format with `cargo fmt`
- Lint with `cargo clippy -- -D warnings`
- Document public APIs with `///` comments
- Use `#[pyclass]` and `#[pymethods]` for Python bindings

### Python
- Format with `black` (line length: 88)
- Sort imports with `isort`
- Add type hints to public APIs
- Use Google-style docstrings

## Testing

```bash
# Run all Python tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_rust_acceleration.py -v

# Run Rust tests
cargo test

# Run with coverage
uv run pytest tests/ --cov=fast_litellm

# Run benchmarks
python scripts/run_benchmarks.py --iterations 100
```

## Benchmarking

Run benchmarks to verify performance:

```bash
# Quick benchmark (50 iterations)
python scripts/run_benchmarks.py --iterations 50

# Full benchmark with memory pressure tests
python scripts/run_benchmarks.py --iterations 200 \
  --memory-texts 100 --memory-text-size 1000 --memory-keys 1000

# Skip concurrent benchmarks for faster runs
python scripts/run_benchmarks.py --iterations 100 --skip-concurrent

# Results are written to BENCHMARK.md and benchmark_results.json
```

## Adding New Rust Functionality

1. Add Rust implementation in `src/*.rs`
2. Export function in `src/lib.rs` with `#[pyfunction]` or `#[pyclass]`
3. Register in the `#[pymodule]` function
4. Rebuild: `uv run maturin develop --release`
5. Add Python wrapper in `fast_litellm/` if needed
6. Add tests in `tests/`
7. Run benchmarks to verify performance

Example adding a new function:

```rust
// src/lib.rs
#[pyfunction]
fn my_new_function(input: String) -> PyResult<String> {
    Ok(format!("Processed: {}", input))
}

#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // ... existing code ...
    m.add_function(wrap_pyfunction!(my_new_function, m)?)?;
    Ok(())
}
```

## Pull Request Process

1. Run full test suite
2. Ensure code is formatted
3. Run benchmarks and verify no significant regressions
4. Update documentation if needed
5. Add tests for new functionality

### PR Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Breaking change

## Testing
- [ ] Tests pass
- [ ] Benchmarks run (no regression)
- [ ] Added tests for new code

## Benchmark Results (if applicable)
| Component | Before | After | Change |
|-----------|--------|-------|--------|
| ... | ... | ... | ... |
```

## Release Process

1. Update version in `Cargo.toml` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full benchmark suite and update `BENCHMARK.md`
4. Create and push a version tag: `git tag v0.x.x && git push origin v0.x.x`
5. CI automatically publishes to PyPI

## Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **CLAUDE.md**: Development guidelines and architecture

## Code of Conduct

Be respectful and constructive in all interactions.
