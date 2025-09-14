#!/usr/bin/env python3
"""
Dedicated performance test to understand caching behavior.
"""

import sys
import os
import time

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_caching_behavior():
    """Test caching behavior to understand performance characteristics."""
    print("=== Testing Caching Behavior ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        # Import Python tiktoken for comparison
        import tiktoken
        
        # Test text and model
        test_text = "This is a test message for performance analysis. " * 20
        model = "gpt-3.5-turbo"
        iterations = 100
        
        print(f"Test text length: {len(test_text)} characters")
        print(f"Model: {model}")
        print(f"Iterations: {iterations}")
        
        # Create token counters
        rust_counter = litellm_token.SimpleTokenCounter(100)
        python_encoder = tiktoken.encoding_for_model(model)
        
        # Test 1: Cold cache performance (first run)
        print("\n--- Cold Cache Performance ---")
        
        # Rust cold cache
        start_time = time.time()
        for i in range(iterations):
            rust_count = rust_counter.count_tokens(test_text, model)
        rust_cold_time = time.time() - start_time
        rust_cold_avg = rust_cold_time / iterations
        
        print(f"Rust cold cache time: {rust_cold_time:.4f}s (avg: {rust_cold_avg*1000:.4f}ms per call)")
        
        # Python cold cache
        start_time = time.time()
        for i in range(iterations):
            python_count = len(python_encoder.encode(test_text))
        python_cold_time = time.time() - start_time
        python_cold_avg = python_cold_time / iterations
        
        print(f"Python cold cache time: {python_cold_time:.4f}s (avg: {python_cold_avg*1000:.4f}ms per call)")
        
        # Test 2: Warm cache performance (second run with cached encodings)
        print("\n--- Warm Cache Performance ---")
        
        # Rust warm cache
        start_time = time.time()
        for i in range(iterations):
            rust_count = rust_counter.count_tokens(test_text, model)
        rust_warm_time = time.time() - start_time
        rust_warm_avg = rust_warm_time / iterations
        
        print(f"Rust warm cache time: {rust_warm_time:.4f}s (avg: {rust_warm_avg*1000:.4f}ms per call)")
        
        # Python warm cache
        start_time = time.time()
        for i in range(iterations):
            python_count = len(python_encoder.encode(test_text))
        python_warm_time = time.time() - start_time
        python_warm_avg = python_warm_time / iterations
        
        print(f"Python warm cache time: {python_warm_time:.4f}s (avg: {python_warm_avg*1000:.4f}ms per call)")
        
        # Test 3: Cache statistics
        print("\n--- Cache Statistics ---")
        cache_stats = rust_counter.get_cache_stats()
        print(f"Rust cache stats: {cache_stats}")
        
        # Performance analysis
        print("\n--- Performance Analysis ---")
        if rust_cold_time > 0 and python_cold_time > 0:
            cold_speedup = python_cold_time / rust_cold_time
            print(f"Cold cache speedup: {cold_speedup:.2f}x (Python/Rust)")
        
        if rust_warm_time > 0 and python_warm_time > 0:
            warm_speedup = python_warm_time / rust_warm_time
            print(f"Warm cache speedup: {warm_speedup:.2f}x (Python/Rust)")
        
        # Check if caching is working
        if rust_warm_avg < rust_cold_avg:
            print("✓ Caching is working - warm cache is faster than cold cache")
        elif rust_warm_avg > rust_cold_avg:
            print("⚠ Caching may not be working optimally - warm cache is slower than cold cache")
        else:
            print("? Caching behavior unclear")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during caching behavior test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_single_call_overhead():
    """Test single call overhead to understand PyO3 bridge cost."""
    print("\n=== Testing Single Call Overhead ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        # Import Python tiktoken for comparison
        import tiktoken
        
        # Test text and model
        test_text = "Hello, world!"
        model = "gpt-3.5-turbo"
        
        # Create token counters
        rust_counter = litellm_token.SimpleTokenCounter(100)
        python_encoder = tiktoken.encoding_for_model(model)
        
        # Time a single call
        iterations = 10000
        
        # Rust single call timing
        start_time = time.time()
        for i in range(iterations):
            rust_count = rust_counter.count_tokens(test_text, model)
        rust_time = time.time() - start_time
        rust_avg = rust_time / iterations
        
        # Python single call timing
        start_time = time.time()
        for i in range(iterations):
            python_count = len(python_encoder.encode(test_text))
        python_time = time.time() - start_time
        python_avg = python_time / iterations
        
        print(f"Single call test with {iterations} iterations")
        print(f"Test text: '{test_text}'")
        print(f"Model: {model}")
        print(f"Rust time: {rust_time:.4f}s (avg: {rust_avg*1000:.4f}ms per call)")
        print(f"Python time: {python_time:.4f}s (avg: {python_avg*1000:.4f}ms per call)")
        
        if python_time > 0:
            speedup = python_time / rust_time
            print(f"Speedup: {speedup:.2f}x (Python/Rust)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during single call overhead test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("LiteLLM Rust Token Counting Caching Behavior Analysis\n")
    
    success1 = test_caching_behavior()
    success2 = test_single_call_overhead()
    
    if success1 and success2:
        print("\n🎉 Caching behavior analysis completed!")
        sys.exit(0)
    else:
        print("\n💥 Caching behavior analysis failed!")
        sys.exit(1)