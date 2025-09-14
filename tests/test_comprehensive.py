#!/usr/bin/env python3
"""
Comprehensive test to compare Rust token counting with Python token counting.
"""

import sys
import os

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_comparison_with_python():
    """Compare Rust token counting with Python token counting."""
    print("=== Comparing Rust vs Python Token Counting ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        # Import Python tiktoken for comparison
        import tiktoken
        
        print("✓ Successfully imported both Rust and Python modules")
        
        # Test cases
        test_cases = [
            ("gpt-3.5-turbo", "Hello, world!"),
            ("gpt-3.5-turbo", "The quick brown fox jumps over the lazy dog."),
            ("gpt-4", "Hello, world!"),
            ("gpt-4", "The quick brown fox jumps over the lazy dog."),
            ("gpt-3.5-turbo", "This is a longer text with more words to test tokenization accuracy."),
            ("gpt-4", "This is a longer text with more words to test tokenization accuracy."),
        ]
        
        # Create token counters
        rust_counter = litellm_token.SimpleTokenCounter(100)
        python_encoders = {}
        
        all_match = True
        
        for model, text in test_cases:
            print(f"\n--- Testing model: {model} ---")
            print(f"Text: {text}")
            
            # Rust token counting
            rust_count = rust_counter.count_tokens(text, model)
            print(f"Rust token count: {rust_count}")
            
            # Python token counting
            if model not in python_encoders:
                python_encoders[model] = tiktoken.encoding_for_model(model)
            python_count = len(python_encoders[model].encode(text))
            print(f"Python token count: {python_count}")
            
            # Compare
            if rust_count == python_count:
                print("✓ Counts match!")
            else:
                print(f"❌ Counts differ! Difference: {abs(rust_count - python_count)}")
                all_match = False
        
        if all_match:
            print("\n🎉 All token counts match between Rust and Python!")
            return True
        else:
            print("\n⚠ Some token counts differ between Rust and Python")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import required modules: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during comparison: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_comparison():
    """Compare performance between Rust and Python token counting."""
    print("\n=== Performance Comparison ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        # Import Python tiktoken for comparison
        import tiktoken
        import time
        
        print("✓ Successfully imported modules for performance test")
        
        # Test text
        test_text = "This is a test text for performance comparison. " * 100
        model = "gpt-3.5-turbo"
        iterations = 1000
        
        # Create token counters
        rust_counter = litellm_token.SimpleTokenCounter(100)
        python_encoder = tiktoken.encoding_for_model(model)
        
        # Test Rust performance
        start_time = time.time()
        for _ in range(iterations):
            rust_count = rust_counter.count_tokens(test_text, model)
        rust_time = time.time() - start_time
        rust_avg = rust_time / iterations
        
        # Test Python performance
        start_time = time.time()
        for _ in range(iterations):
            python_count = len(python_encoder.encode(test_text))
        python_time = time.time() - start_time
        python_avg = python_time / iterations
        
        # Results
        print(f"Test text length: {len(test_text)} characters")
        print(f"Iterations: {iterations}")
        print(f"Rust time: {rust_time:.4f}s (avg: {rust_avg*1000:.4f}ms per call)")
        print(f"Python time: {python_time:.4f}s (avg: {python_avg*1000:.4f}ms per call)")
        
        if python_time > 0:
            speedup = python_time / rust_time
            print(f"Speedup: {speedup:.2f}x faster with Rust")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during performance test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Comprehensive LiteLLM Token Counting Test\n")
    
    success1 = test_comparison_with_python()
    success2 = test_performance_comparison()
    
    if success1 and success2:
        print("\n🎉 All comprehensive tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some comprehensive tests failed!")
        sys.exit(1)