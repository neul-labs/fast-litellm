# Fast LiteLLM Makefile
# Provides convenient commands for development, testing, and building

# Variables
PYTHON := python3
PIP := pip3
MATURIN := maturin
PROJECT_ROOT := .
LITELLM_DIR := $(PROJECT_ROOT)/.litellm

# Detect virtual environment
ifeq ($(VIRTUAL_ENV),)
	ifneq ($(wildcard .venv/bin/activate),)
		VENV_ACTIVATE := .venv/bin/activate
		export VIRTUAL_ENV := $(abspath .venv)
		export PATH := $(abspath .venv/bin):$(PATH)
	endif
endif

# Help target
.PHONY: help
help:  ## Show this help message
	@echo "Fast LiteLLM - High-performance Rust acceleration for LiteLLM"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@grep -E '^[a-zA-Z_0-9%-]+:.*?## .*$$' $(word 1,$(MAKEFILE_LIST)) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-30s %s\n", $$1, $$2}'

# Development environment setup
.PHONY: setup setup-dev setup-litellm
setup setup-dev:  ## Setup development environment
	@echo "Setting up development environment..."
	@if [ -f "scripts/setup_dev.sh" ]; then \
		bash scripts/setup_dev.sh; \
	else \
		echo "Setting up manually..."; \
		$(PIP) install --upgrade pip; \
		$(PIP) install maturin; \
		$(PIP) install -e ".[dev]"; \
		$(MATURIN) develop; \
	fi

setup-litellm:  ## Setup LiteLLM for integration testing
	@echo "Setting up LiteLLM for integration testing..."
	@if [ -f "scripts/setup_litellm.sh" ]; then \
		bash scripts/setup_litellm.sh; \
	else \
		echo "scripts/setup_litellm.sh not found"; \
		exit 1; \
	fi

# Building targets
.PHONY: build develop rebuild clean
build:  ## Build Rust extensions in release mode
	@echo "Building Rust extensions in release mode..."
	$(MATURIN) build --release

develop:  ## Build Rust extensions in development mode (for fast iteration)
	@echo "Building Rust extensions in development mode..."
	$(MATURIN) develop

rebuild: clean develop  ## Clean and rebuild Rust extensions

clean:  ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	cargo clean
	rm -rf target/
	rm -rf dist/
	rm -rf build/

# Testing targets
.PHONY: test test-unit test-integration test-benchmark
test:  ## Run all tests
	@echo "Running all tests..."
	pytest tests/ -v

test-unit:  ## Run unit tests only
	@echo "Running unit tests..."
	pytest tests/test_rust_acceleration.py -v

test-integration:  ## Run integration tests
	@echo "Running integration tests..."
	pytest tests/test_rust_code_paths.py -v

test-benchmark:  ## Run benchmark comparisons
	@echo "Running benchmark tests..."
	python scripts/benchmark_token_counting.py --iterations 10

# Integration testing with LiteLLM
.PHONY: integration-test litellm-test
integration-test litellm-test:  ## Run LiteLLM tests with Fast LiteLLM acceleration
	@echo "Running LiteLLM integration tests with acceleration..."
	@if [ -f "scripts/run_litellm_tests.sh" ]; then \
		bash scripts/run_litellm_tests.sh; \
	else \
		echo "scripts/run_litellm_tests.sh not found"; \
		exit 1; \
	fi

# Benchmarking targets
.PHONY: benchmark benchmark-compare benchmark-profile token-benchmark comprehensive-benchmark shimmed-benchmark before-after-benchmark all-benchmarks
benchmark:  ## Run general performance benchmarks
	@echo "Running performance benchmarks..."
	bash scripts/run_benchmark_tests.sh

benchmark-compare:  ## Run benchmark comparison (baseline vs accelerated)
	@echo "Running benchmark comparison..."
	bash scripts/run_benchmark_tests.sh --benchmark-mode compare

benchmark-profile:  ## Run detailed profiling
	@echo "Running detailed performance profiling..."
	bash scripts/run_benchmark_tests.sh --benchmark-mode profile

token-benchmark:  ## Run specific token counting benchmark (default: compare all modes)
	@echo "Running token counting benchmark (compare mode)..."
	python scripts/benchmark_token_counting.py --mode compare

token-benchmark-direct:  ## Run token counting benchmark (direct Rust calls only)
	@echo "Running direct Rust token counting benchmark..."
	python scripts/benchmark_token_counting.py --mode direct

token-benchmark-shimmed:  ## Run token counting benchmark (shimmed functions only)
	@echo "Running shimmed token counting benchmark..."
	python scripts/benchmark_token_counting.py --mode shimmed

shimmed-benchmark:  ## Run actual shimmed performance benchmark
	@echo "Running actual shimmed performance benchmark..."
	python scripts/benchmark_shimmed_performance.py --mode compare

before-after-benchmark:  ## Run before/after shimming comparison benchmark
	@echo "Running before/after shimming comparison benchmark..."
	python scripts/benchmark_before_after_shimming.py

comprehensive-benchmark:  ## Run comprehensive benchmark of all shimmed functions (1000 iterations)
	@echo "Running comprehensive benchmark of all shimmed functions (1000 iterations)..."
	python scripts/benchmark_comprehensive_shimmed.py --iterations 1000

all-benchmarks:  ## Run all benchmark types
	@echo "Running all benchmark types..."
	@$(MAKE) benchmark
	@$(MAKE) token-benchmark
	@$(MAKE) shimmed-benchmark
	@$(MAKE) before-after-benchmark
	@$(MAKE) comprehensive-benchmark

# Code quality targets
.PHONY: format lint type-check quality
format:  ## Format code with black
	@echo "Formatting code with black..."
	black fast_litellm/ tests/ scripts/

lint:  ## Lint code with ruff
	@echo "Linting code with ruff..."
	ruff check fast_litellm/ tests/ scripts/
	ruff format --check fast_litellm/ tests/ scripts/

type-check:  ## Run type checking with mypy
	@echo "Running type checking with mypy..."
	mypy fast_litellm/ --config-file pyproject.toml

quality: format lint type-check  ## Run all code quality checks

# Documentation
.PHONY: docs docs-build docs-serve
docs docs-build:  ## Build documentation
	@echo "Building documentation..."
	$(PIP) install .[docs]
	# Documentation build commands would go here

# Package management
.PHONY: install install-dev uninstall
install:  ## Install package in current environment
	@echo "Installing package..."
	pip install .

install-dev:  ## Install package in development mode
	@echo "Installing package in development mode..."
	pip install -e .

uninstall:  ## Uninstall package
	@echo "Uninstalling package..."
	pip uninstall -y fast-litellm

# Distribution
.PHONY: dist dist-check release
dist: clean  ## Build distribution packages
	@echo "Building distribution packages..."
	$(MATURIN) build
	ls -la dist/

dist-check: dist  ## Check distribution packages
	@echo "Checking distribution packages..."
	twine check dist/*

release: dist-check  ## Build and validate release packages
	@echo "Preparing release packages..."
	@echo "Run 'maturin publish' to publish to PyPI"

# Utility targets
.PHONY: shell check-env check-rust
shell:  ## Start Python shell with Fast LiteLLM imported
	@echo "Starting Python shell with Fast LiteLLM imported..."
	$(PYTHON) -c "import fast_litellm; print(f'Fast LiteLLM {fast_litellm.__version__} loaded'); print(f'Rust acceleration: {fast_litellm.RUST_ACCELERATION_AVAILABLE}'); import IPython as ip; ip.start_ipython(argv=[])" || $(PYTHON) -i -c "import fast_litellm; print(f'Fast LiteLLM {fast_litellm.__version__} loaded'); print(f'Rust acceleration: {fast_litellm.RUST_ACCELERATION_AVAILABLE}')"

check-env:  ## Check development environment setup
	@echo "Checking development environment..."
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Maturin: $(shell $(MATURIN) --version 2>/dev/null || echo 'not installed')"
	@echo "Rust: $(shell rustc --version 2>/dev/null || echo 'not installed')"
	@echo "Virtual environment: $(VIRTUAL_ENV)"
	@if python -c "import fast_litellm._rust" 2>/dev/null; then \
		echo "Rust extensions: ✅ Available"; \
	else \
		echo "Rust extensions: ❌ Not available"; \
	fi

check-rust:  ## Check Rust build environment
	@echo "Checking Rust build environment..."
	@echo "Rust: $(shell rustc --version)"
	@echo "Cargo: $(shell cargo --version)"
	@echo "Maturin: $(shell maturin --version 2>/dev/null || echo 'not installed')"
	@cargo check || echo "⚠️  Cargo check failed - Rust dependencies may need to be installed"

# Performance monitoring
.PHONY: perf-monitor perf-status
perf-monitor:  ## Show current performance monitoring status
	@echo "Current performance monitoring status:"
	$(PYTHON) -c "import fast_litellm; print('Fast LiteLLM Performance Status:'); import json; print(json.dumps(fast_litellm.get_performance_stats(), indent=2))"

perf-status:  ## Show feature flag status
	@echo "Current feature flag status:"
	$(PYTHON) -c "import fast_litellm; print('Feature Flag Status:'); import json; print(json.dumps(fast_litellm.get_feature_status(), indent=2))"

# Clean up targets
.PHONY: clean-pyc clean-test clean-build
clean-pyc:  ## Remove Python file artifacts
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

clean-test:  ## Remove test artifacts
	rm -f .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -f fast_litellm_benchmark_results.json
	rm -f baseline_results.json
	rm -f accelerated_results.json

clean-build: clean-pyc clean-test  ## Remove all build artifacts

# Default target
all: setup test  ## Setup and run tests (default target)