#!/bin/bash
set -e

echo "🔧 Setting up litellm-rust development environment"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found. Please install Python 3.8 or later."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Found Python $python_version"

# Check if Rust is available
if ! command -v cargo &> /dev/null; then
    echo "❌ Error: Rust not found. Please install Rust from https://rustup.rs/"
    exit 1
fi

rust_version=$(rustc --version)
echo "🦀 Found Rust: $rust_version"

# Install or upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install maturin
echo "🔨 Installing maturin..."
python3 -m pip install maturin

# Install development dependencies
echo "📚 Installing development dependencies..."
python3 -m pip install -e ".[dev]"

# Build the Rust extensions in development mode
echo "🏗️  Building Rust extensions in development mode..."
maturin develop

# Run basic tests
echo "🧪 Running basic tests..."
python3 -m pytest tests/ -v

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🚀 Quick start commands:"
echo "  maturin develop     # Rebuild Rust extensions"
echo "  pytest tests/       # Run tests"
echo "  maturin build       # Build release wheel"
echo "  python scripts/test_package.py  # Test full build and install"
echo ""