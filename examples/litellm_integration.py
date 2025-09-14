#!/usr/bin/env python3
"""
Example showing how to use LiteLLM Rust acceleration with actual LiteLLM.
"""

def main():
    print("LiteLLM Rust Acceleration with LiteLLM Integration")
    print("=" * 50)
    
    # First, import the acceleration (this will automatically apply it)
    try:
        import litellm_rust
        print("✓ LiteLLM Rust Acceleration imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import LiteLLM Rust Acceleration: {e}")
        return
    
    # Check if Rust acceleration is available
    if litellm_rust.RUST_ACCELERATION_AVAILABLE:
        print("✓ Rust acceleration is available and automatically applied")
    else:
        print("✗ Rust acceleration is not available")
        return
    
    # Import LiteLLM to see if classes have been patched
    try:
        import litellm
        print("✓ LiteLLM imported successfully")
        
        # Check if specific classes exist
        if hasattr(litellm, 'SimpleTokenCounter'):
            print("✓ SimpleTokenCounter class is available")
        else:
            print("? SimpleTokenCounter class not found")
            
        if hasattr(litellm, 'SimpleRateLimiter'):
            print("✓ SimpleRateLimiter class is available")
        else:
            print("? SimpleRateLimiter class not found")
            
        if hasattr(litellm, 'SimpleConnectionPool'):
            print("✓ SimpleConnectionPool class is available")
        else:
            print("? SimpleConnectionPool class not found")
            
    except ImportError as e:
        print(f"✗ Failed to import LiteLLM: {e}")
        return
    
    # Demonstrate token counting acceleration
    print("\nDemonstrating accelerated token counting:")
    try:
        # Try to use the Rust-accelerated token counter
        counter = litellm.SimpleTokenCounter(100)
        
        # Count tokens in a sample text
        sample_text = "The quick brown fox jumps over the lazy dog. " * 10
        token_count = counter.count_tokens(sample_text, "gpt-3.5-turbo")
        print(f"✓ Token count for sample text: {token_count}")
        
    except Exception as e:
        print(f"✗ Token counting failed: {e}")
    
    # Demonstrate rate limiting acceleration
    print("\nDemonstrating accelerated rate limiting:")
    try:
        # Try to use the Rust-accelerated rate limiter
        limiter = litellm.SimpleRateLimiter()
        
        # Check rate limit
        user_key = "user_12345"
        within_limit = limiter.check_rate_limit(user_key, 100, 60)  # 100 requests per 60 seconds
        print(f"✓ Rate limit check for {user_key}: {within_limit}")
        
    except Exception as e:
        print(f"✗ Rate limiting failed: {e}")
    
    # Demonstrate health checks
    print("\nDemonstrating health checks:")
    try:
        health = litellm_rust.health_check()
        print(f"✓ Overall system health check: {health.get('overall_healthy', 'Unknown')}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")

if __name__ == "__main__":
    main()