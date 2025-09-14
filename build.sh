#!/bin/bash

# Build script for LiteLLM Rust Acceleration

set -e  # Exit on any error

echo "Building LiteLLM Rust Acceleration..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Please run this script from the project root directory."
    exit 1
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build the package
echo "Building Python package..."
python -m build

echo "Build completed successfully!"
echo "Distribution files are in the 'dist/' directory."