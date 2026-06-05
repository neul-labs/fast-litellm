# Contributing

Fast LiteLLM is maintained by Dipankar Sarkar at [Neul Labs](https://www.neul.uk) ([me@dipankar.name](mailto:me@dipankar.name)). Contributions are welcome.

## Prerequisites

- Python 3.8+ (3.12 recommended)
- Rust toolchain 1.70+ (`rustup` recommended)
- [uv](https://docs.astral.sh/uv/) for package management
- Git

## Quick Setup

```bash
git clone https://github.com/neul-labs/fast-litellm.git
cd fast-litellm

# Run the setup script (installs uv if needed)
./scripts/setup_dev.sh
```

## Manual Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

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

2. Rebuild after Rust changes:
   ```bash
   uv run maturin develop --release
   ```

3. Run tests:
   ```bash
   uv run pytest tests/ -v
   cargo test
   ```

4. Format and lint:
   ```bash
   uv run black fast_litellm/ tests/
   uv run isort fast_litellm/ tests/
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

# Run a specific test file
uv run pytest tests/test_rust_acceleration.py -v

# Run Rust tests
cargo test

# Coverage
uv run pytest tests/ --cov=fast_litellm

# Benchmarks
python scripts/run_benchmarks.py --iterations 100
```

### LiteLLM Integration Tests

```bash
# Setup LiteLLM for testing
./scripts/setup_litellm.sh

# Run LiteLLM tests with acceleration enabled
./scripts/run_litellm_tests.sh

# Compare performance with vs without acceleration
./scripts/compare_performance.py
```

## Adding a New Rust Function

1. Implement in `src/<module>.rs`.
2. Export in `src/lib.rs` with `#[pyfunction]` (or `#[pyclass]` for types).
3. Register it inside the `#[pymodule]` function.
4. Rebuild: `uv run maturin develop --release`.
5. Add a Python wrapper in `fast_litellm/` if needed.
6. Add tests in `tests/`.
7. Run benchmarks to verify performance.

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

## Pull Requests

Before opening a PR:

- Run the full test suite
- Ensure code is formatted (`cargo fmt`, `black`, `isort`)
- Run benchmarks; confirm no significant regressions
- Update documentation under `documentation/docs/` when behaviour changes
- Add tests for new functionality

## Release Process

1. Update version in `Cargo.toml` (`pyproject.toml` reads it dynamically via maturin).
2. Update `CHANGELOG.md`.
3. Run the full benchmark suite and update `BENCHMARK.md`.
4. Tag the release: `git tag v0.x.x && git push origin v0.x.x`.
5. CI publishes to PyPI automatically.

## Code of Conduct

Be respectful and constructive in all interactions.
