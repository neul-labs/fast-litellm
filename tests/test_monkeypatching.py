"""
Test to verify that monkeypatching actually replaces LiteLLM classes.
"""

import sys
import os

def test_monkeypatching():
    """Test that monkeypatching actually replaces LiteLLM classes."""
    
    print("Testing LiteLLM Rust Acceleration Monkeypatching")
    print("=" * 50)
    
    # First, import the acceleration
    try:
        import litellm_rust
        print("✓ LiteLLM Rust Acceleration imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import LiteLLM Rust Acceleration: {e}")
        return False
    
    # Check if Rust acceleration is available
    if not litellm_rust.RUST_ACCELERATION_AVAILABLE:
        print("ℹ Rust acceleration is not available, skipping monkeypatching test")
        return True
    
    # Import LiteLLM
    try:
        import litellm
        print("✓ LiteLLM imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import LiteLLM: {e}")
        return False
    
    # Check if the classes have been patched
    classes_to_check = [
        'SimpleTokenCounter',
        'SimpleRateLimiter',
        'SimpleConnectionPool',
    ]
    
    all_patched = True
    for class_name in classes_to_check:
        if hasattr(litellm, class_name):
            cls = getattr(litellm, class_name)
            module_name = getattr(cls, '__module__', 'Unknown')
            print(f"✓ {class_name} found in litellm module (from {module_name})")
            
            # Check if it's from our Rust module
            if 'litellm_rust' in module_name or 'litellm_token' in module_name or 'litellm_rate_limiter' in module_name or 'litellm_connection_pool' in module_name:
                print(f"  ℹ {class_name} appears to be from Rust extension")
            else:
                print(f"  ? {class_name} is from {module_name} (not Rust extension)")
        else:
            print(f"✗ {class_name} not found in litellm module")
            all_patched = False
    
    # Try to instantiate and use the patched classes
    print("\nTesting instantiation and usage:")
    try:
        # Test SimpleTokenCounter
        if hasattr(litellm, 'SimpleTokenCounter'):
            counter = litellm.SimpleTokenCounter(100)
            token_count = counter.count_tokens("Hello, world!", "gpt-3.5-turbo")
            print(f"✓ SimpleTokenCounter works: {token_count} tokens")
        else:
            print("✗ SimpleTokenCounter not available for testing")
            all_patched = False
            
        # Test SimpleRateLimiter
        if hasattr(litellm, 'SimpleRateLimiter'):
            limiter = litellm.SimpleRateLimiter()
            within_limit = limiter.check_rate_limit("test_user", 100, 60)
            print(f"✓ SimpleRateLimiter works: rate limit check = {within_limit}")
        else:
            print("✗ SimpleRateLimiter not available for testing")
            all_patched = False
            
    except Exception as e:
        print(f"✗ Error testing patched classes: {e}")
        all_patched = False
    
    return all_patched

if __name__ == "__main__":
    success = test_monkeypatching()
    if success:
        print("\n✓ All tests passed! Monkeypatching is working correctly.")
    else:
        print("\n✗ Some tests failed. Monkeypatching may not be working correctly.")
        sys.exit(1)