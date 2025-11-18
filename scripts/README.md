# Fast LiteLLM Scripts

This directory contains scripts for development, testing, and benchmarking Fast LiteLLM.

## Setup Scripts

- `setup_dev.sh` - Complete development environment setup
- `setup_litellm.sh` - Setup LiteLLM for integration testing

## Testing Scripts

- `run_litellm_tests.sh` - Run LiteLLM's test suite with Fast LiteLLM acceleration enabled
- `run_benchmark_tests.sh` - Run comprehensive benchmark tests with performance analysis
- `test_package.py` - Test full package build and installation
- `test_rust.sh` - Test Rust extensions and functionality

## Benchmarking Scripts

- `benchmark_token_counting.py` - Specific benchmark for token counting performance
- `compare_performance.py` - Compare performance with/without Fast LiteLLM acceleration

## Usage

### Running Integration Tests
```bash
# Run LiteLLM tests with acceleration
./scripts/run_litellm_tests.sh [test_path]

# Example: Run specific test file
./scripts/run_litellm_tests.sh tests/unit/test_embedding.py
```

### Running Benchmark Tests
```bash
# Run benchmark tests with acceleration
./scripts/run_benchmark_tests.sh [options] [test_path]

# Examples:
./scripts/run_benchmark_tests.sh                           # Run default benchmarks
./scripts/run_benchmark_tests.sh --benchmark-mode compare  # Compare with baseline
./scripts/run_benchmark_tests.sh --benchmark-min-rounds 20 # Custom rounds
```

### Running Token Counting Benchmarks
```bash
# Run token counting benchmark
python scripts/benchmark_token_counting.py --iterations 100

# Save results to JSON
python scripts/benchmark_token_counting.py --output results.json
```

### Setup Development Environment
```bash
# One-time setup
./scripts/setup_dev.sh

# Or step-by-step setup
pip install maturin
maturin develop
pytest tests/
```

## Environment Variables

Several environment variables can be used to control the behavior:

- `LITELLM_RUST_DISABLE_ALL` - Disable all Rust features
- `LITELLM_RUST_FEATURE_CONFIG` - Path to feature config file
- `FAST_LITELLM_BATCH_TOKEN_COUNTING` - Configure batch token counting feature
- `FAST_LITELLM_RUST_ROUTING` - Enable/disable Rust routing

## Performance Monitoring

Fast LiteLLM includes comprehensive performance monitoring capabilities:

- Automatic performance tracking for all accelerated features
- Feature flag-based control for gradual rollout
- Performance-based automatic fallback
- Export functionality for detailed analysis