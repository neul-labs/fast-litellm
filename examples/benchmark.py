#!/usr/bin/env python3
"""
Benchmark script to demonstrate performance improvements from Rust acceleration.
"""

import time
import litellm_rust

def benchmark_token_counting():
    """Benchmark token counting performance."""
    if not litellm_rust.RUST_ACCELERATION_AVAILABLE:
        print("Rust acceleration not available, skipping benchmark")
        return
    
    from litellm_rust.rust_extensions import litellm_token
    counter = litellm_token.SimpleTokenCounter(100)
    
    # Sample text for benchmarking
    sample_text = "The quick brown fox jumps over the lazy dog. " * 100
    iterations = 1000
    
    # Benchmark Rust token counting
    start_time = time.time()
    for _ in range(iterations):
        counter.count_tokens(sample_text, "gpt-3.5-turbo")
    rust_time = time.time() - start_time
    
    print(f"Rust token counting: {iterations} iterations in {rust_time:.4f} seconds")
    print(f"Rust token counting: {iterations/rust_time:.2f} operations/second")
    
    # Note: We can't easily benchmark the Python version without it,
    # but in practice the Rust version should be significantly faster

def benchmark_rate_limiting():
    """Benchmark rate limiting performance."""
    if not litellm_rust.RUST_ACCELERATION_AVAILABLE:
        print("Rust acceleration not available, skipping benchmark")
        return
    
    from litellm_rust.rust_extensions import litellm_rate_limiter
    limiter = litellm_rate_limiter.SimpleRateLimiter()
    
    iterations = 10000
    
    # Benchmark Rust rate limiting
    start_time = time.time()
    for i in range(iterations):
        limiter.check_rate_limit(f"user_{i}", 100, 60)
    rust_time = time.time() - start_time
    
    print(f"Rust rate limiting: {iterations} iterations in {rust_time:.4f} seconds")
    print(f"Rust rate limiting: {iterations/rust_time:.2f} operations/second")

def main():
    print("LiteLLM Rust Acceleration Benchmarks")
    print("=" * 40)
    
    benchmark_token_counting()
    print()
    benchmark_rate_limiting()

if __name__ == "__main__":
    main()