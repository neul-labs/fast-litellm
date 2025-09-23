# Contributing to LiteLLM Rust

Thank you for your interest in contributing to LiteLLM Rust! This guide will help you get started with development and contributing to the project.

## Development Setup

### Prerequisites

- **Python 3.8+** with pip
- **Rust toolchain 1.70+** (`rustup` recommended)
- **Git** for version control
- **LiteLLM** for integration testing

### Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/litellm-rust.git
   cd litellm-rust
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Rust toolchain** (if not already installed):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source ~/.cargo/env
   ```

5. **Verify setup**:
   ```bash
   make test-quick
   ```

## Project Structure

```
litellm-rust/
├── litellm-core/           # Rust: Advanced routing
├── litellm-token/          # Rust: Token counting
├── litellm-connection-pool/# Rust: Connection management
├── litellm-rate-limiter/   # Rust: Rate limiting
├── litellm_rust/           # Python: Integration layer
│   ├── enhanced_monkeypatch.py
│   ├── feature_flags.py
│   ├── performance_monitor.py
│   └── ...
├── examples/               # Usage examples
├── docs/                   # Documentation
├── tests/                  # Test suite
├── config/                 # Configuration templates
└── Makefile               # Development commands
```

## Development Workflow

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards below

3. **Run tests**:
   ```bash
   make test-all
   ```

4. **Format code**:
   ```bash
   make format
   ```

5. **Run linters**:
   ```bash
   make lint
   ```

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

## Coding Standards

### Rust Code

- **Format**: Use `cargo fmt` (enforced by CI)
- **Linting**: Use `cargo clippy` with default lints
- **Documentation**: Document all public APIs with `///` comments
- **Error handling**: Use `thiserror` for error types
- **Async**: Use `tokio` for async operations

**Example**:
```rust
/// Count tokens for multiple texts in batch
#[pyo3(signature = (texts, model))]
fn count_tokens_batch(&self, _py: Python, texts: Vec<&str>, model: &str) -> PyResult<Vec<usize>> {
    debug!("Batch counting tokens for {} texts", texts.len());
    // Implementation...
}
```

### Python Code

- **Format**: Use `black` (line length: 88)
- **Import sorting**: Use `isort`
- **Type hints**: Required for all public APIs
- **Documentation**: Use Google-style docstrings

**Example**:
```python
def record_performance(
    component: str,
    operation: str,
    duration_ms: float,
    success: bool = True,
    **kwargs
) -> None:
    """Record a performance metric.

    Args:
        component: Component name (e.g., 'rust_routing')
        operation: Operation name (e.g., 'route_request')
        duration_ms: Duration in milliseconds
        success: Whether the operation was successful
        **kwargs: Additional metadata
    """
    # Implementation...
```

### Commit Message Format

Use conventional commits:

- `feat: add new feature`
- `fix: bug fix`
- `docs: documentation update`
- `style: formatting changes`
- `refactor: code refactoring`
- `test: add tests`
- `chore: maintenance tasks`

## Testing

### Running Tests

```bash
# Quick smoke tests
make test-quick

# Full test suite
make test-all

# Rust-only tests
make test-rust

# Python-only tests
make test-python

# Performance benchmarks
make benchmark
```

### Writing Tests

#### Rust Tests
Place tests in `src/` files or `tests/` directory:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_token_counting() {
        let counter = SimpleTokenCounter::new(100);
        let count = counter.count_tokens("hello world", "gpt-3.5-turbo").unwrap();
        assert!(count > 0);
    }
}
```

#### Python Tests
Use pytest in the `tests/` directory:

```python
import pytest
import litellm_rust

def test_feature_flag_enabled():
    """Test feature flag functionality."""
    assert isinstance(litellm_rust.is_enabled("rust_routing"), bool)

@pytest.mark.asyncio
async def test_async_wrapper():
    """Test async wrapper functionality."""
    # Async test implementation
```

## Performance Considerations

### Optimization Guidelines

1. **Minimize allocations**: Reuse buffers and data structures
2. **Avoid blocking**: Use async operations for I/O
3. **Batch operations**: Process multiple items together when possible
4. **Cache strategically**: Cache expensive computations
5. **Profile regularly**: Use `cargo bench` and `pytest-benchmark`

### Benchmarking

```bash
# Rust benchmarks
cd litellm-token
cargo bench

# Python benchmarks
pytest tests/benchmarks/ -v
```

## Documentation

### API Documentation

- **Rust**: Use `cargo doc` to generate documentation
- **Python**: Use Sphinx with Google-style docstrings

### Documentation Updates

When adding new features:

1. Update relevant `.md` files in `docs/`
2. Add examples to `examples/`
3. Update API reference in `docs/api.md`
4. Update configuration docs if applicable

## Debugging

### Debug Builds

```bash
# Debug Rust components
export RUST_LOG=debug
python -c "import litellm_rust; print('Debug enabled')"

# Enable performance monitoring
export LITELLM_RUST_PERFORMANCE_MONITORING=true
```

### Common Issues

1. **PyO3 binding errors**: Check Python/Rust type compatibility
2. **Performance regressions**: Run benchmarks before/after changes
3. **Memory leaks**: Use `valgrind` or similar tools
4. **Thread safety**: Review concurrent access patterns

## Pull Request Process

### Before Submitting

1. **Run full test suite**: `make test-all`
2. **Check formatting**: `make format`
3. **Run linters**: `make lint`
4. **Update documentation**: If adding new features
5. **Add tests**: For new functionality

### PR Description Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Benchmarks show no regression

## Documentation
- [ ] Updated API docs
- [ ] Updated examples
- [ ] Updated configuration docs

## Additional Notes
Any additional information or context
```

### Review Process

1. **Automated checks**: CI runs tests and linting
2. **Code review**: Maintainer reviews code quality
3. **Performance review**: Check for performance regressions
4. **Documentation review**: Ensure docs are updated

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `Cargo.toml` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Create release PR
5. Tag release after merge
6. Publish to PyPI and crates.io

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and improve
- Follow project conventions

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Documentation**: Check docs first
- **Examples**: Look at example code

### Becoming a Maintainer

Regular contributors who demonstrate:

- Code quality and testing discipline
- Good communication and collaboration
- Understanding of project goals
- Commitment to helping others

May be invited to become maintainers.

## Advanced Topics

### Adding New Rust Components

1. Create new crate in workspace
2. Add to `Cargo.toml` workspace members
3. Implement PyO3 bindings
4. Add Python integration layer
5. Update monkeypatching system
6. Add comprehensive tests

### Performance Optimization

1. Profile with `cargo flamegraph`
2. Identify bottlenecks
3. Implement optimizations
4. Benchmark improvements
5. Validate with integration tests

### Feature Flag Implementation

1. Add feature to `feature_flags.py`
2. Update configuration schema
3. Add environment variable support
4. Implement gradual rollout logic
5. Add monitoring and alerts

Thank you for contributing to LiteLLM Rust! Your contributions help make high-performance LLM operations accessible to everyone.