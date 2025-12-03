#!/bin/bash
set -e

echo "Setting up fast-litellm development environment"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.8 or later."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Found Python $python_version"

# Check if Rust is available
if ! command -v cargo &> /dev/null; then
    echo "Error: Rust not found. Please install Rust from https://rustup.rs/"
    exit 1
fi

rust_version=$(rustc --version)
echo "Found Rust: $rust_version"

# Check if uv is available, install if not
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the shell config to get uv in PATH
    export PATH="$HOME/.cargo/bin:$PATH"
    if ! command -v uv &> /dev/null; then
        echo "Error: Failed to install uv. Please install it manually from https://docs.astral.sh/uv/"
        exit 1
    fi
fi

uv_version=$(uv --version)
echo "Found uv: $uv_version"

# Create virtual environment with uv
echo "Creating virtual environment..."
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install maturin
echo "Installing maturin..."
uv add --dev maturin

# Install development dependencies
echo "Installing development dependencies..."
uv sync --all-extras

# Build the Rust extensions in development mode
echo "Building Rust extensions in development mode..."
uv run maturin develop

# Run basic tests
echo "Running basic tests..."
uv run pytest tests/ -v

echo ""
echo "Development environment setup complete!"
echo ""
echo "Quick start commands:"
echo "  source .venv/bin/activate  # Activate virtual environment"
echo "  uv run maturin develop     # Rebuild Rust extensions"
echo "  uv run pytest tests/       # Run tests"
echo "  uv run maturin build       # Build release wheel"
echo "  uv run python scripts/test_package.py  # Test full build and install"
echo ""
