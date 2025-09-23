# PyPI Deployment Guide

This document outlines the PyPI packaging and deployment setup for litellm-rust.

## 🚀 Package Overview

The litellm-rust package is now ready for PyPI distribution with the following features:

- **Unified Rust Extension**: Single Python extension module built with maturin
- **Professional Documentation**: Developer-focused README and organized docs/
- **Comprehensive CI/CD**: GitHub Actions workflows for testing and publishing
- **Type Safety**: Full type hints and PEP 561 compliance
- **Cross-Platform**: Builds for Linux, Windows, and macOS

## 📦 Package Structure

```
litellm-rust/
├── litellm_rust/           # Python package
│   ├── __init__.py         # Main package with Rust imports
│   ├── __init__.pyi        # Type stubs
│   └── py.typed            # PEP 561 marker
├── src/                    # Rust source code
│   ├── lib.rs              # Main Rust module
│   ├── core.rs             # Advanced routing
│   ├── tokens.rs           # Token counting
│   ├── connection_pool.rs  # Connection management
│   ├── rate_limiter.rs     # Rate limiting
│   ├── feature_flags.rs    # Feature flag system
│   └── performance_monitor.rs # Performance tracking
├── pyproject.toml          # Package configuration
├── Cargo.toml              # Rust configuration
├── MANIFEST.in             # Source distribution rules
├── .github/workflows/      # CI/CD workflows
│   ├── ci.yml              # Testing and linting
│   └── release.yml         # PyPI publishing
└── docs/                   # Documentation
```

## 🛠️ Build System

The package uses **maturin** as the build backend for Rust-Python integration:

```toml
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[tool.maturin]
python-source = "litellm_rust"
module-name = "litellm_rust._rust"
features = ["pyo3/extension-module"]
```

## 🏗️ Building the Package

### Local Development Build
```bash
# Install maturin
pip install maturin

# Development build (creates editable install)
maturin develop

# Release build
maturin build --release --out dist
```

### Automated CI/CD Build

The package includes two GitHub Actions workflows:

#### 1. Continuous Integration (`ci.yml`)
- **Triggers**: Push to main/develop, pull requests
- **Matrix**: Linux, Windows, macOS × Python 3.8-3.12
- **Jobs**:
  - `test`: Build package, run pytest with coverage
  - `lint`: Black, isort, flake8, mypy, rustfmt, clippy
  - `security`: cargo audit, safety checks

#### 2. Release Publishing (`release.yml`)
- **Triggers**: Git tags (`v*`) or manual dispatch
- **Jobs**:
  - `build-wheels`: Cross-platform wheel building
  - `build-sdist`: Source distribution
  - `test-release`: Test PyPI deployment (manual only)
  - `release`: Production PyPI deployment (tags only)

## 📋 Package Configuration

### Core Dependencies
```toml
dependencies = [
    "pydantic>=1.10.0",
    "tiktoken>=0.5.0",
    "aiohttp>=3.8.0",
    "httpx>=0.24.0",
]
```

### Development Dependencies
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "maturin>=1.0.0",
]
```

## 🚀 Publishing Workflow

### Automated Release Process

1. **Create a Git Tag**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. **GitHub Actions Automatically**:
   - Builds wheels for all platforms
   - Creates source distribution
   - Publishes to PyPI
   - Creates GitHub release

### Manual Test Release

1. **Trigger Test Release**:
   - Go to GitHub Actions
   - Run "Release" workflow manually
   - Specify version (e.g., "0.1.0")
   - Publishes to Test PyPI

2. **Test Installation**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ litellm-rust
   ```

## 🔧 Development Setup

### Quick Start
```bash
# Clone repository
git clone https://github.com/BerriAI/litellm-rust
cd litellm-rust

# Run setup script
./scripts/setup_dev.sh
```

### Manual Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev]"

# Build Rust extensions
maturin develop

# Run tests
pytest tests/
```

## 🧪 Testing

The package includes comprehensive testing:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=litellm_rust --cov-report=html

# Run only fast tests
pytest tests/ -m "not slow"

# Test specific functionality
pytest tests/test_basic.py::test_import_package
```

## 📊 Package Verification

### Installation Test
```python
import litellm_rust

# Check version
print(f"Version: {litellm_rust.__version__}")

# Check Rust acceleration
print(f"Rust available: {litellm_rust.RUST_ACCELERATION_AVAILABLE}")

# Basic functionality
health = litellm_rust.health_check()
print(f"Health: {health}")
```

### Performance Verification
```python
import litellm_rust

# Record performance
litellm_rust.record_performance(
    component="test",
    operation="example",
    duration_ms=10.5
)

# Get statistics
stats = litellm_rust.get_performance_stats()
print(stats)
```

## 🔐 Security Setup

### Required Secrets

For automated publishing, configure these GitHub repository secrets:

- `PYPI_API_TOKEN`: PyPI API token for production releases
- `TEST_PYPI_API_TOKEN`: Test PyPI token for test releases

### Token Creation
1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Create API token with project scope
3. Add to GitHub repository secrets

## 📈 Monitoring

The package includes comprehensive monitoring:

- **Performance Metrics**: Real-time component performance tracking
- **Feature Flags**: Gradual rollout and canary deployments
- **Error Handling**: Automatic fallback to Python implementations
- **Health Checks**: System status and component availability

## 🔄 Versioning Strategy

The project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Version is automatically extracted from Git tags during CI/CD.

## 📝 Release Checklist

Before creating a release:

- [ ] Update CHANGELOG.md with new features/fixes
- [ ] Ensure all tests pass locally
- [ ] Update documentation if needed
- [ ] Create and push Git tag
- [ ] Verify automated release succeeds
- [ ] Test installation from PyPI
- [ ] Announce release

## 🎉 Success!

The litellm-rust package is now fully configured for PyPI distribution with:

✅ Professional package structure
✅ Cross-platform Rust compilation
✅ Comprehensive CI/CD pipeline
✅ Automated testing and security checks
✅ Type safety and documentation
✅ Performance monitoring and feature flags

The package is ready for production deployment and can be installed via:

```bash
pip install litellm-rust
```