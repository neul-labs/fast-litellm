# Makefile for LiteLLM Rust Acceleration

.PHONY: build build-release test clean install develop check help

# Default target
help:
	@echo "LiteLLM Rust Acceleration Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  build         - Build the Python package"
	@echo "  build-release - Build the Python package in release mode"
	@echo "  test          - Run Python tests"
	@echo "  test-rust     - Run Rust tests"
	@echo "  test-all      - Run all tests"
	@echo "  clean         - Clean build artifacts"
	@echo "  install       - Install the package"
	@echo "  develop       - Install the package in development mode"
	@echo "  check         - Check Rust code"
	@echo "  fmt           - Format Rust code"
	@echo "  help          - Show this help message"

# Build the Python package
build:
	./build.sh

# Build in release mode
build-release:
	cargo build --release

# Run Python tests
test:
	python -m pytest tests/ -v

# Run Rust tests
test-rust:
	cargo test

# Run all tests
test-all: test-rust test

# Clean build artifacts
clean:
	cargo clean
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -name "*.so" -delete
	find . -name "*.dylib" -delete
	find . -name "*.dll" -delete

# Install the package
install:
	pip install .

# Install in development mode
develop:
	pip install -e .

# Check Rust code
check:
	cargo check

# Format Rust code
fmt:
	cargo fmt