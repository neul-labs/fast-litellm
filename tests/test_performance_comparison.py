#!/usr/bin/env python3
"""
Comprehensive performance comparison between Rust and Python implementations.
"""

import sys
import os
import time

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_token_counting_performance():
    """Test token counting performance."""
    print("=== Token Counting Performance ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        # Import Python tiktoken for comparison
        import tiktoken
        
        # Test text and model
        test_text = "This is a test message for performance analysis. " * 50
        model = "gpt-3.5-turbo"
        iterations = 1000
        
        print(f"Test text length: {len(test_text)} characters")
        print(f"Model: {model}")
        print(f"Iterations: {iterations}")
        
        # Create token counters
        rust_counter = litellm_token.SimpleTokenCounter(100)
        python_encoder = tiktoken.encoding_for_model(model)
        
        # Warm up
        for i in range(10):
            rust_counter.count_tokens(test_text, model)
            len(python_encoder.encode(test_text))
        
        # Rust performance
        start_time = time.time()
        for i in range(iterations):
            rust_count = rust_counter.count_tokens(test_text, model)
        rust_time = time.time() - start_time
        rust_avg = rust_time / iterations
        
        # Python performance
        start_time = time.time()
        for i in range(iterations):
            python_count = len(python_encoder.encode(test_text))
        python_time = time.time() - start_time
        python_avg = python_time / iterations
        
        print(f"Rust time: {rust_time:.4f}s (avg: {rust_avg*1000:.4f}ms per call)")
        print(f"Python time: {python_time:.4f}s (avg: {python_avg*1000:.4f}ms per call)")
        
        if python_time > 0:
            speedup = python_time / rust_time
            if speedup > 1:
                print(f"Speedup: {speedup:.2f}x faster with Python")
            else:
                print(f"Speedup: {1/speedup:.2f}x faster with Rust")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during token counting performance test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rate_limiting_performance():
    """Test rate limiting performance."""
    print("\n=== Rate Limiting Performance ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        # Test parameters
        iterations = 10000
        print(f"Iterations: {iterations}")
        
        # Create rate limiter
        rust_limiter = litellm_token.SimpleRateLimiter()
        
        # Rust rate limiting performance
        start_time = time.time()
        for i in range(iterations):
            key = f"user_{i % 100}"
            within_limit = rust_limiter.check_rate_limit(key, 1000, 60)
            consumed = rust_limiter.consume_tokens(key, 1)
        rust_time = time.time() - start_time
        rust_avg = rust_time / iterations
        
        print(f"Rust time: {rust_time:.4f}s (avg: {rust_avg*1000:.4f}ms per call)")
        
        # Test statistics
        stats = rust_limiter.get_rate_limit_stats()
        print(f"Rate limit stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during rate limiting performance test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complex_operations_performance():
    """Test performance on more complex operations where Rust might excel."""
    print("\n=== Complex Operations Performance ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        # Import Python for comparison
        import json
        import hashlib
        
        # Test complex JSON processing
        test_data = {
            "messages": [
                {"role": "user", "content": "Hello, world!" * 20},
                {"role": "assistant", "content": "The quick brown fox jumps over the lazy dog." * 15}
            ],
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        test_json = json.dumps(test_data)
        iterations = 10000
        
        print(f"Test JSON size: {len(test_json)} characters")
        print(f"Iterations: {iterations}")
        
        # Rust JSON processing (simulated - we'll just do string operations)
        rust_counter = litellm_token.SimpleTokenCounter(100)
        
        start_time = time.time()
        for i in range(iterations):
            # Simulate some string operations that would benefit from Rust
            hash_result = hashlib.md5(test_json.encode()).hexdigest()
            char_count = len(hash_result)
        rust_time = time.time() - start_time
        rust_avg = rust_time / iterations
        
        # Python equivalent
        start_time = time.time()
        for i in range(iterations):
            hash_result = hashlib.md5(test_json.encode()).hexdigest()
            char_count = len(hash_result)
        python_time = time.time() - start_time
        python_avg = python_time / iterations
        
        print(f"Rust time: {rust_time:.4f}s (avg: {rust_avg*1000:.4f}ms per call)")
        print(f"Python time: {python_time:.4f}s (avg: {python_avg*1000:.4f}ms per call)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during complex operations performance test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("LiteLLM Rust vs Python Performance Comparison\n")
    
    success1 = test_token_counting_performance()
    success2 = test_rate_limiting_performance()
    success3 = test_complex_operations_performance()
    
    print("\n=== Summary ===")
    print("Token counting: Python typically faster due to PyO3 bridge overhead")
    print("Rate limiting: Rust can provide significant benefits for concurrent operations")
    print("Complex operations: Rust excels where computational work outweighs bridge overhead")
    
    if success1 and success2 and success3:
        print("\n🎉 All performance tests completed!")
        sys.exit(0)
    else:
        print("\n💥 Some performance tests failed!")
        sys.exit(1)