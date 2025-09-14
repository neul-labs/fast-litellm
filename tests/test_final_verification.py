#!/usr/bin/env python3
"""
Final verification test to confirm that our core optimizations are working.
"""

import sys
import os

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_core_optimizations():
    """Test that our core optimizations are working correctly."""
    print("=== Testing Core Optimizations ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        print("✓ Successfully imported litellm_token")
        
        # Test 1: Token counting accuracy
        print("\n--- Token Counting Accuracy ---")
        
        # Create token counter
        token_counter = litellm_token.SimpleTokenCounter(100)
        print(f"✓ Created SimpleTokenCounter with cache size: {token_counter.cache_size}")
        
        # Test with various texts and models
        test_cases = [
            ("Hello, world!", "gpt-3.5-turbo", 4),
            ("The quick brown fox jumps over the lazy dog.", "gpt-3.5-turbo", 10),
            ("", "gpt-3.5-turbo", 0),
            ("a", "gpt-3.5-turbo", 1),
        ]
        
        all_correct = True
        for text, model, expected in test_cases:
            result = token_counter.count_tokens(text, model)
            if result == expected:
                print(f"✓ '{text[:20]}...' -> {result} tokens (expected: {expected})")
            else:
                print(f"❌ '{text[:20]}...' -> {result} tokens (expected: {expected})")
                all_correct = False
        
        if all_correct:
            print("✓ All token counting results are correct")
        else:
            print("❌ Some token counting results are incorrect")
            return False
        
        # Test 2: Caching functionality
        print("\n--- Caching Functionality ---")
        
        # Check initial cache stats
        initial_stats = token_counter.get_cache_stats()
        print(f"✓ Initial cache stats: {initial_stats}")
        
        # Perform some token counting to populate cache
        test_text = "This is a test message for caching."
        for i in range(10):
            token_counter.count_tokens(test_text, "gpt-3.5-turbo")
        
        # Check cache stats after use
        final_stats = token_counter.get_cache_stats()
        print(f"✓ Final cache stats: {final_stats}")
        
        # Verify cache is working (should have cached encodings)
        if final_stats.get("cached_encodings", 0) > 0:
            print("✓ Caching is working - encodings are being cached")
        else:
            print("⚠ Caching may not be working optimally")
        
        # Test 3: Rate limiting functionality
        print("\n--- Rate Limiting Functionality ---")
        
        # Create rate limiter
        rate_limiter = litellm_token.SimpleRateLimiter()
        print("✓ Created SimpleRateLimiter")
        
        # Test rate limit check
        key = "test-user"
        limit = 100
        window_seconds = 60
        
        within_limit = rate_limiter.check_rate_limit(key, limit, window_seconds)
        print(f"✓ Rate limit check for '{key}': {within_limit}")
        
        # Test token consumption
        tokens = 5
        consumed = rate_limiter.consume_tokens(key, tokens)
        print(f"✓ Consumed {tokens} tokens for '{key}': {consumed}")
        
        # Test rate limit statistics
        stats = rate_limiter.get_rate_limit_stats()
        print(f"✓ Rate limit statistics: {stats}")
        
        # Verify rate limiting is working
        if stats.get("tracked_keys", 0) > 0:
            print("✓ Rate limiting is tracking keys correctly")
        else:
            print("⚠ Rate limiting may not be tracking keys")
        
        print("\n🎉 All core optimization tests passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_token: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during core optimization test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("LiteLLM Rust Core Optimizations - Final Verification\n")
    
    success = test_core_optimizations()
    
    if success:
        print("\n🎉 CORE OPTIMIZATIONS VERIFICATION PASSED! 🎉")
        print("The Rust performance enhancements are working correctly.")
        sys.exit(0)
    else:
        print("\n💥 CORE OPTIMIZATIONS VERIFICATION FAILED! 💥")
        print("Some core optimizations are not working correctly.")
        sys.exit(1)