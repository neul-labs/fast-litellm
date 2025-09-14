#!/usr/bin/env python3
"""
Test script to verify that the token counting implementation works correctly.
"""

import sys
import os

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_token_counting():
    """Test that the token counting functionality works correctly."""
    print("=== Testing Token Counting Functionality ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        print("✓ Successfully imported litellm_token")
        
        # Test health check
        health = litellm_token.token_health_check()
        print(f"✓ Health check returned: {health}")
        
        # Test token counter creation
        token_counter = litellm_token.SimpleTokenCounter(100)
        print(f"✓ Created SimpleTokenCounter with cache size: {token_counter.cache_size}")
        
        # Test basic token counting
        text = "Hello, world! This is a test message."
        model = "gpt-3.5-turbo"
        
        token_count = token_counter.count_tokens(text, model)
        print(f"✓ Counted tokens for '{text}' with model '{model}': {token_count}")
        
        # Test batch token counting
        texts = [
            "Hello, world!",
            "This is a test message.",
            "Another example text for token counting."
        ]
        
        batch_counts = token_counter.count_tokens_batch(texts, model)
        print(f"✓ Batch token counting for {len(texts)} texts: {batch_counts}")
        
        # Test cache statistics
        cache_stats = token_counter.get_cache_stats()
        print(f"✓ Cache statistics: {cache_stats}")
        
        print("\n🎉 Token counting test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_token: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing token counting: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rate_limiting():
    """Test that the rate limiting functionality works correctly."""
    print("\n=== Testing Rate Limiting Functionality ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        # Test rate limiter creation
        rate_limiter = litellm_token.SimpleRateLimiter()
        print("✓ Created SimpleRateLimiter")
        
        # Test rate limit check
        key = "test-user"
        limit = 10
        window_seconds = 60
        
        within_limit = rate_limiter.check_rate_limit(key, limit, window_seconds)
        print(f"✓ Rate limit check for key '{key}': {within_limit}")
        
        # Test token consumption
        tokens = 5
        success = rate_limiter.consume_tokens(key, tokens)
        print(f"✓ Consumed {tokens} tokens for key '{key}': {success}")
        
        # Test rate limit statistics
        stats = rate_limiter.get_rate_limit_stats()
        print(f"✓ Rate limit statistics: {stats}")
        
        print("\n🎉 Rate limiting test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_token: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing rate limiting: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing LiteLLM Rust Token Counting Components\n")
    
    success1 = test_token_counting()
    success2 = test_rate_limiting()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)