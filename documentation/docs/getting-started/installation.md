# Installation

Fast LiteLLM can be installed using pip or uv. Prebuilt wheels are available for all major platforms, so Rust is not required for installation.

## Requirements

- Python 3.8 or higher (3.12 recommended)
- LiteLLM (will be installed automatically if not present)

## Installing from PyPI

### Using uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that we recommend:

```bash
uv add fast-litellm
```

### Using pip

```bash
pip install fast-litellm
```

## Verifying Installation

After installation, verify that Rust acceleration is available:

```python
import fast_litellm

if fast_litellm.RUST_ACCELERATION_AVAILABLE:
    print("Rust acceleration is available!")
else:
    print("Falling back to Python implementations")
```

You can also run a health check:

```python
import fast_litellm

health = fast_litellm.health_check()
print(f"Status: {health['status']}")
print(f"Components: {health['components']}")
```

## Platform Support

Prebuilt wheels are available for:

| Platform | Architecture | Status |
|----------|--------------|--------|
| Linux | x86_64 | Supported |
| Linux | aarch64 | Supported |
| macOS | x86_64 | Supported |
| macOS | ARM64 (M1/M2) | Supported |
| Windows | x86_64 | Supported |

## Building from Source

If you need to build from source (for development or unsupported platforms):

### Prerequisites

- Python 3.8+
- Rust toolchain (1.70+)
- [maturin](https://www.maturin.rs/) for building Python extensions

### Steps

1. Install Rust:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/neul-labs/fast-litellm.git
   cd fast-litellm
   ```

3. Create a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install maturin and build:
   ```bash
   uv add --dev maturin
   uv run maturin develop --release
   ```

5. Verify the build:
   ```bash
   python -c "import fast_litellm; print(fast_litellm.RUST_ACCELERATION_AVAILABLE)"
   ```

## Troubleshooting

### Import Errors

If you encounter import errors:

1. Ensure you're using a supported Python version (3.8+)
2. Try reinstalling: `pip install --force-reinstall fast-litellm`
3. Check for conflicting packages: `pip list | grep litellm`

### Rust Extensions Not Loading

If `RUST_ACCELERATION_AVAILABLE` is `False`:

1. Check for any import warnings that may indicate the issue
2. Ensure your platform has prebuilt wheels available
3. Try building from source following the steps above

### Virtual Environment Issues

Always use a virtual environment to avoid conflicts:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fast-litellm
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Start using Fast LiteLLM
- [Configuration](../guides/configuration.md) - Configure advanced options
