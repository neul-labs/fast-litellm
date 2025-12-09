# Compatibility

This document outlines the supported versions, platforms, and compatibility information for Fast LiteLLM.

## Python Versions

| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.9 | Supported | Minimum supported version |
| 3.10 | Supported | Fully tested |
| 3.11 | Supported | Fully tested |
| 3.12 | Supported | Fully tested |
| 3.13 | Supported | Fully tested |
| 3.14+ | Not Supported | Waiting for PyO3 support |

**Note:** Python 3.8 was dropped due to dependency requirements (flake8 6.0+ requires Python 3.8.1+, and newer tooling requires 3.9+).

## Platforms

### Linux

| Architecture | Status | Wheel Available |
|--------------|--------|-----------------|
| x86_64 (amd64) | Supported | Yes (manylinux2014) |
| aarch64 (ARM64) | Supported | Yes (manylinux2014) |

### macOS

| Architecture | Status | Wheel Available |
|--------------|--------|-----------------|
| x86_64 (Intel) | Supported | Yes |
| aarch64 (Apple Silicon) | Supported | Yes |

### Windows

| Architecture | Status | Wheel Available |
|--------------|--------|-----------------|
| x86_64 (64-bit) | Supported | Yes |
| x86 (32-bit) | Not Supported | No |
| ARM64 | Not Supported | No |

## Dependencies

### Runtime Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| pydantic | >=1.10.0 | Data validation |
| tiktoken | >=0.5.0 | Token counting |
| aiohttp | >=3.8.0 | Async HTTP client |
| httpx | >=0.24.0 | HTTP client |

### Build Dependencies (Development Only)

| Dependency | Version | Purpose |
|------------|---------|---------|
| maturin | >=1.0,<2.0 | Build system for PyO3 |
| Rust | >=1.70 | Compiler |
| PyO3 | 0.24 | Python-Rust bindings |

## LiteLLM Compatibility

Fast LiteLLM is designed to work with the latest stable release of LiteLLM. Compatibility is tested on every commit via CI.

| LiteLLM Version | Status |
|-----------------|--------|
| Latest stable | Tested in CI |
| Previous releases | Best effort |

## Rust Dependencies

Key Rust crates used:

| Crate | Version | Purpose |
|-------|---------|---------|
| pyo3 | 0.24 | Python bindings |
| tokio | 1.0 | Async runtime |
| dashmap | 6.0 | Lock-free concurrent maps |
| tiktoken-rs | 0.7.0 | Token counting |
| serde | 1.0 | Serialization |

## Security

- All dependencies are regularly audited via `cargo audit`
- PyO3 0.24+ is required to address security vulnerability RUSTSEC-2025-0020

## CI/CD Matrix

The following configurations are tested in CI:

### Main CI Workflow

| OS | Python Versions |
|----|-----------------|
| Ubuntu (latest) | 3.9, 3.10, 3.11, 3.12 |
| Windows (latest) | 3.10, 3.11, 3.12 |
| macOS (latest) | 3.10, 3.11, 3.12 |

### Compatibility Tests

| OS | Python Version | LiteLLM Version |
|----|----------------|-----------------|
| Ubuntu (latest) | 3.11 | Latest |
| Windows (latest) | 3.11 | Latest |
| macOS (latest) | 3.11 | Latest |

### Publish Workflow

Wheels are built for:

| OS | Python Versions | Architectures |
|----|-----------------|---------------|
| Linux | 3.9, 3.10, 3.11, 3.12, 3.13 | x86_64, aarch64 |
| Windows | 3.9, 3.10, 3.11, 3.12, 3.13 | x86_64 |
| macOS | 3.9, 3.10, 3.11, 3.12, 3.13 | x86_64, aarch64 |

## Known Limitations

1. **Python 3.14**: Not yet supported as PyO3 0.24 only supports up to Python 3.13
2. **Windows ARM64**: No wheel available due to limited CI support
3. **32-bit systems**: Not supported

## Reporting Issues

If you encounter compatibility issues, please:

1. Check this document for known limitations
2. Search existing [GitHub issues](https://github.com/neul-labs/fast-litellm/issues)
3. Open a new issue with:
   - Python version (`python --version`)
   - Platform and architecture (`python -c "import platform; print(platform.platform())"`)
   - LiteLLM version (`pip show litellm`)
   - Fast LiteLLM version (`pip show fast-litellm`)
   - Full error traceback
