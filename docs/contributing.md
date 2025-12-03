# Contributing to Fast LiteLLM

Thank you for your interest in contributing!

## Development Setup

### Prerequisites

- Python 3.8+
- Rust toolchain 1.70+ (`rustup` recommended)
- uv for package management
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
source .venv/bin/activate

# Install dependencies
uv sync --all-extras

# Build Rust extensions
uv run maturin develop
```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make changes and run tests:
   ```bash
   uv run pytest tests/ -v
   cargo test
   ```

3. Format and lint:
   ```bash
   uv run black .
   uv run isort .
   cargo fmt
   cargo clippy
   ```

4. Commit using conventional commits:
   ```bash
   git commit -m "feat: add your feature"
   ```

## Coding Standards

### Rust
- Format with `cargo fmt`
- Lint with `cargo clippy`
- Document public APIs with `///` comments

### Python
- Format with `black` (line length: 88)
- Sort imports with `isort`
- Add type hints to public APIs
- Use Google-style docstrings

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run Rust tests
cargo test

# Run with coverage
uv run pytest tests/ --cov=fast_litellm
```

## Pull Request Process

1. Run full test suite
2. Ensure code is formatted
3. Update documentation if needed
4. Add tests for new functionality

### PR Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change

## Testing
- [ ] Tests pass
- [ ] Added tests for new code
```

## Release Process

1. Update version in `Cargo.toml` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create and push a version tag: `git tag v0.x.x && git push origin v0.x.x`
4. CI automatically publishes to PyPI

## Getting Help

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and community support
