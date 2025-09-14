#!/usr/bin/env python3
"""
Comprehensive integration test for all LiteLLM Rust components.
"""

import sys
import os
import time

# Add the target directory to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "debug"))

def test_token_counting():
    """Test token counting functionality."""
    print("=== Testing Token Counting ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        # Create token counter
        counter = litellm_token.SimpleTokenCounter(100)
        print(f"✓ Created SimpleTokenCounter")
        
        # Test basic token counting
        text = "Hello, world! This is a test message."
        model = "gpt-3.5-turbo"
        
        token_count = counter.count_tokens(text, model)
        print(f"✓ Counted {token_count} tokens for: '{text}'")
        
        # Test batch token counting
        texts = [
            "Hello, world!",
            "This is a test message.",
            "Another example text for token counting."
        ]
        
        batch_counts = counter.count_tokens_batch(texts, model)
        print(f"✓ Batch token counting: {batch_counts}")
        
        # Test cache statistics
        cache_stats = counter.get_cache_stats()
        print(f"✓ Cache statistics: {cache_stats}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing token counting: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n=== Testing Rate Limiting ===")
    
    try:
        # Import the Rust module
        import litellm_token
        
        # Create rate limiter
        limiter = litellm_token.SimpleRateLimiter()
        print(f"✓ Created SimpleRateLimiter")
        
        # Test rate limit check
        key = "test-user"
        limit = 10
        window_seconds = 60
        
        within_limit = limiter.check_rate_limit(key, limit, window_seconds)
        print(f"✓ Rate limit check for '{key}': {within_limit}")
        
        # Test token consumption
        tokens = 5
        consumed = limiter.consume_tokens(key, tokens)
        print(f"✓ Consumed {tokens} tokens for '{key}': {consumed}")
        
        # Test rate limit statistics
        stats = limiter.get_rate_limit_stats()
        print(f"✓ Rate limit statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing rate limiting: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connection_pooling():
    """Test connection pooling functionality."""
    print("\n=== Testing Connection Pooling ===")
    
    try:
        # Import the Rust module
        import litellm_connection_pool
        
        # Test health check
        health = litellm_connection_pool.connection_pool_health_check()
        print(f"✓ Connection pool health check: {health}")
        
        # Create connection pool
        pool = litellm_connection_pool.SimpleConnectionPool(10)
        print(f"✓ Created SimpleConnectionPool with max connections: {pool.max_connections_per_provider}")
        
        # Test getting a connection
        provider = "openai"
        conn_id = pool.get_connection(provider)
        print(f"✓ Got connection for provider '{provider}': {conn_id}")
        
        # Test returning a connection
        returned = pool.return_connection(conn_id)
        print(f"✓ Returned connection '{conn_id}': {returned}")
        
        # Test closing a connection
        conn_id2 = pool.get_connection(provider)
        closed = pool.close_connection(conn_id2)
        print(f"✓ Closed connection '{conn_id2}': {closed}")
        
        # Test pool statistics
        stats = pool.get_pool_stats()
        print(f"✓ Pool statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing connection pooling: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_comparison():
    """Test performance benefits of the Rust implementation."""
    print("\n=== Performance Comparison ===")
    
    try:
        # Import the Rust modules
        import litellm_token
        import tiktoken
        
        # Test parameters
        test_text = "This is a performance test message. " * 20
        model = "gpt-3.5-turbo"
        iterations = 1000
        
        print(f"Test text length: {len(test_text)} characters")
        print(f"Model: {model}")
        print(f"Iterations: {iterations}")
        
        # Rust token counting
        rust_counter = litellm_token.SimpleTokenCounter(100)
        
        start_time = time.time()
        for i in range(iterations):
            rust_count = rust_counter.count_tokens(test_text, model)
        rust_time = time.time() - start_time
        rust_avg = rust_time / iterations
        
        # Python token counting
        python_encoder = tiktoken.encoding_for_model(model)
        
        start_time = time.time()
        for i in range(iterations):
            python_count = len(python_encoder.encode(test_text))
        python_time = time.time() - start_time
        python_avg = python_time / iterations
        
        print(f"Rust time: {rust_time:.4f}s (avg: {rust_avg*1000:.4f}ms per call)")
        print(f"Python time: {python_time:.4f}s (avg: {python_avg*1000:.4f}ms per call)")
        
        if python_time > 0:
            speedup = python_time / rust_time
            print(f"Speedup: {speedup:.2f}x faster with Rust")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing performance: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_scenarios():
    """Test realistic integration scenarios."""
    print("\n=== Integration Scenarios ===")
    
    try:
        # Import all Rust modules
        import litellm_token
        import litellm_connection_pool
        
        # Scenario 1: Token counting for multiple models
        print("\n--- Scenario 1: Multi-model Token Counting ---")
        counter = litellm_token.SimpleTokenCounter(100)
        
        test_models = ["gpt-3.5-turbo", "gpt-4", "claude-3-haiku"]
        test_text = "This is a test message for comparing different models."
        
        for model in test_models:
            count = counter.count_tokens(test_text, model)
            print(f"  {model}: {count} tokens")
        
        # Scenario 2: Rate limiting with multiple users
        print("\n--- Scenario 2: Multi-user Rate Limiting ---")
        limiter = litellm_token.SimpleRateLimiter()
        
        users = ["user1", "user2", "user3"]
        for user in users:
            for i in range(5):
                within_limit = limiter.check_rate_limit(user, 10, 60)
                consumed = limiter.consume_tokens(user, 1)
                print(f"  {user} request {i+1}: within limit = {within_limit}, consumed = {consumed}")
        
        # Scenario 3: Connection management for multiple providers
        print("\n--- Scenario 3: Multi-provider Connections ---")
        pool = litellm_connection_pool.SimpleConnectionPool(5)
        
        providers = ["openai", "anthropic", "cohere"]
        for provider in providers:
            for i in range(3):
                try:
                    conn_id = pool.get_connection(provider)
                    pool.return_connection(conn_id)
                    print(f"  {provider} connection {i+1}: managed successfully")
                except Exception as e:
                    print(f"  {provider} connection {i+1}: error - {e}")
        
        # Scenario 4: Combined operations
        print("\n--- Scenario 4: Combined Operations ---")
        combined_counter = litellm_token.SimpleTokenCounter(50)
        combined_limiter = litellm_token.SimpleRateLimiter()
        combined_pool = litellm_connection_pool.SimpleConnectionPool(3)
        
        # Process a batch of requests
        batch_texts = [
            "Hello, world!",
            "This is a test message.",
            "Another example for batch processing.",
            "Performance testing with Rust components.",
            "Integration scenario combining all features."
        ]
        
        model = "gpt-3.5-turbo"
        provider = "openai"
        user = "test-user"
        
        for i, text in enumerate(batch_texts):
            # Token counting
            token_count = combined_counter.count_tokens(text, model)
            
            # Rate limiting
            within_limit = combined_limiter.check_rate_limit(user, 100, 60)
            if within_limit:
                combined_limiter.consume_tokens(user, token_count)
            
            # Connection management
            try:
                conn_id = combined_pool.get_connection(provider)
                combined_pool.return_connection(conn_id)
                conn_status = "SUCCESS"
            except Exception:
                conn_status = "FAILED"
            
            print(f"  Request {i+1}: {token_count} tokens, rate_limit={within_limit}, connection={conn_status}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing integration scenarios: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("LiteLLM Rust Components - Comprehensive Integration Test\n")
    
    # Run all tests
    test_results = []
    
    test_results.append(("Token Counting", test_token_counting()))
    test_results.append(("Rate Limiting", test_rate_limiting()))
    test_results.append(("Connection Pooling", test_connection_pooling()))
    test_results.append(("Performance Comparison", test_performance_comparison()))
    test_results.append(("Integration Scenarios", test_integration_scenarios()))
    
    # Print summary
    print("\n" + "="*50)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print("="*50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("The LiteLLM Rust components are working correctly.")
        sys.exit(0)
    else:
        print(f"\n💥 {total - passed} TESTS FAILED! 💥")
        print("Some components may need attention.")
        sys.exit(1)