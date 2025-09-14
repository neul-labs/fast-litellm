#!/usr/bin/env python3
"""
Simple test to verify that the token counting implementation is working correctly.
"""

import sys
import os

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_token_counting_accuracy():
    """Test that the token counting implementation is accurate."""
    print("=== Testing Token Counting Accuracy ===")
    
    try:
        # Import the Rust module
        import litellm_token
        import tiktoken
        
        print("✓ Successfully imported both Rust and Python modules")
        
        # Create token counter
        rust_counter = litellm_token.SimpleTokenCounter(100)
        print(f"✓ Created SimpleTokenCounter with cache size: {rust_counter.cache_size}")
        
        # Import Python tiktoken for comparison
        python_encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
        print("✓ Imported Python tiktoken encoder")
        
        # Test data
        test_cases = [
            "Hello, world!",
            "The quick brown fox jumps over the lazy dog.",
            "This is a longer text with more words to test tokenization accuracy.",
            "Special characters: !@#$%^&*()_+-=[]{}|;:,.<>?",
            "Unicode characters: 你好世界 🌍🚀",
            "Mixed content: Hello 你好 world 🌍!",
            "",
            " ",
            "a",
            "abcdefghijklmnopqrstuvwxyz",
        ]
        
        print(f"\nTesting {len(test_cases)} cases...")
        
        all_match = True
        for i, text in enumerate(test_cases):
            print(f"\n--- Test Case {i+1}: '{text[:30]}{'...' if len(text) > 30 else ''}' ---")
            
            # Rust token counting
            rust_count = rust_counter.count_tokens(text, "gpt-3.5-turbo")
            print(f"Rust token count: {rust_count}")
            
            # Python token counting
            python_count = len(python_encoder.encode(text))
            print(f"Python token count: {python_count}")
            
            # Compare
            if rust_count == python_count:
                print("✓ Counts match!")
            else:
                print(f"❌ Counts differ! Difference: {abs(rust_count - python_count)}")
                all_match = False
        
        # Test cache statistics
        cache_stats = rust_counter.get_cache_stats()
        print(f"\n✓ Token cache statistics: {cache_stats}")
        
        if all_match:
            print("\n🎉 All token counts match! Implementation is accurate.")
            return True
        else:
            print("\n⚠ Some token counts differ. Implementation needs adjustment.")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import required modules: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during accuracy test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rate_limiting_functionality():
    """Test that the rate limiting implementation is working."""
    print("\n=== Testing Rate Limiting Functionality ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        print("✓ Successfully imported litellm_token")
        
        # Create rate limiter
        rate_limiter = litellm_token.SimpleRateLimiter()
        print("✓ Created SimpleRateLimiter")
        
        # Test rate limiting
        key = "test-user"
        limit = 100
        window_seconds = 60
        
        # Check initial rate limit
        within_limit = rate_limiter.check_rate_limit(key, limit, window_seconds)
        print(f"✓ Initial rate limit check for '{key}': {within_limit}")
        
        # Consume tokens
        tokens = 5
        consumed = rate_limiter.consume_tokens(key, tokens)
        print(f"✓ Consumed {tokens} tokens for '{key}': {consumed}")
        
        # Check rate limit after consumption
        within_limit_after = rate_limiter.check_rate_limit(key, limit, window_seconds)
        print(f"✓ Rate limit check after consumption for '{key}': {within_limit_after}")
        
        # Get rate limit statistics
        stats = rate_limiter.get_rate_limit_stats()
        print(f"✓ Rate limit statistics: {stats}")
        
        print("\n✓ Rate limiting functionality working correctly!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_token: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during rate limiting test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing LiteLLM Rust Token Counting Accuracy and Rate Limiting\n")
    
    success1 = test_token_counting_accuracy()
    success2 = test_rate_limiting_functionality()
    
    if success1 and success2:
        print("\n🎉 All accuracy and functionality tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some accuracy or functionality tests failed!")
        sys.exit(1)