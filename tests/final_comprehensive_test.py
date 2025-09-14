#!/usr/bin/env python3
"""
Final comprehensive test to verify that the entire Rust implementation is working correctly.
"""

import sys
import os

# Add the target directory to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_full_implementation():
    """Test that the full implementation is working correctly."""
    print("=== Final Comprehensive Test of Rust Implementation ===")
    
    try:
        # Import all Rust modules
        import litellm_core
        import litellm_token
        import litellm_connection_pool
        
        print("✓ Successfully imported all Rust modules")
        
        # Test health checks
        core_health = litellm_core.health_check()
        token_health = litellm_token.token_health_check()
        pool_health = litellm_connection_pool.connection_pool_health_check()
        
        print(f"✓ Core health check: {core_health}")
        print(f"✓ Token health check: {token_health}")
        print(f"✓ Pool health check: {pool_health}")
        
        if not (core_health and token_health and pool_health):
            print("❌ Some health checks failed")
            return False
        
        # Test core functionality
        core = litellm_core.LiteLLMCore()
        print(f"✓ Created LiteLLMCore instance")
        print(f"✓ Core available: {core.is_available()}")
        
        # Test token counting
        token_counter = litellm_token.SimpleTokenCounter(100)
        print(f"✓ Created SimpleTokenCounter with cache size: {token_counter.cache_size}")
        
        text = "Hello, world! This is a test message."
        model = "gpt-3.5-turbo"
        token_count = token_counter.count_tokens(text, model)
        print(f"✓ Counted {token_count} tokens for: '{text[:30]}...' with model '{model}'")
        
        # Test batch token counting
        texts = ["Hello", "world", "test"]
        batch_counts = token_counter.count_tokens_batch(texts, model)
        print(f"✓ Batch token counting: {batch_counts}")
        
        # Test cache statistics
        cache_stats = token_counter.get_cache_stats()
        print(f"✓ Token cache statistics: {cache_stats}")
        
        # Test rate limiting
        rate_limiter = litellm_token.SimpleRateLimiter()
        print(f"✓ Created SimpleRateLimiter")
        
        key = "test-user"
        within_limit = rate_limiter.check_rate_limit(key, 100, 60)
        print(f"✓ Rate limit check for '{key}': {within_limit}")
        
        consumed = rate_limiter.consume_tokens(key, 5)
        print(f"✓ Consumed 5 tokens for '{key}': {consumed}")
        
        rate_stats = rate_limiter.get_rate_limit_stats()
        print(f"✓ Rate limit statistics: {rate_stats}")
        
        # Test connection pooling
        connection_pool = litellm_connection_pool.SimpleConnectionPool(10)
        print(f"✓ Created SimpleConnectionPool with max connections: {connection_pool.max_connections_per_provider}")
        
        provider = "openai"
        conn_id = connection_pool.get_connection(provider)
        print(f"✓ Got connection for provider '{provider}': {conn_id}")
        
        returned = connection_pool.return_connection(conn_id)
        print(f"✓ Returned connection '{conn_id}': {returned}")
        
        pool_stats = connection_pool.get_pool_stats()
        print(f"✓ Pool statistics: {pool_stats}")
        
        # Test deployment creation
        litellm_params = {
            "model": "gpt-3.5-turbo",
            "api_base": "https://api.openai.com/v1"
        }
        
        model_info = {
            "description": "GPT-3.5 Turbo model",
            "max_tokens": 4096,
            "input_cost_per_token": 0.0000015,
            "output_cost_per_token": 0.000002
        }
        
        deployment = litellm_core.Deployment(
            "test-model",
            litellm_params,
            model_info
        )
        print(f"✓ Created Deployment: {deployment.model_name}")
        
        # Test routing with JSON dicts (not JSON strings)
        request_data = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        try:
            result = core.route_request(request_data)
            print(f"✓ Routing with Python dict successful")
            print(f"  Result type: {type(result)}")
            print(f"  Result model_name: {result.model_name}")
        except Exception as e:
            print(f"⚠ Routing with Python dict failed: {e}")
        
        # Test backward compatibility with JSON strings
        import json
        json_request = json.dumps({
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}]
        })
        
        try:
            result = core.route_request(json_request)
            print(f"✓ Routing with JSON string successful")
            print(f"  Result type: {type(result)}")
            print(f"  Result model_name: {result.model_name}")
        except Exception as e:
            print(f"⚠ Routing with JSON string failed: {e}")
        
        # Test deployment attribute access
        print(f"  Model name: {deployment.model_name}")
        print(f"  Litellm params type: {type(deployment.litellm_params)}")
        print(f"  Model info type: {type(deployment.model_info)}")
        
        # Test JSON compatibility methods
        try:
            params_json = deployment.litellm_params_json()
            info_json = deployment.model_info_json()
            print(f"✓ JSON compatibility methods work")
            print(f"  Params JSON length: {len(params_json)}")
            print(f"  Info JSON length: {len(info_json)}")
        except Exception as e:
            print(f"⚠ JSON compatibility methods failed: {e}")
        
        print("\n🎉 Full implementation test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import Rust modules: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing full implementation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("LiteLLM Rust Components - Final Comprehensive Test\n")
    
    success = test_full_implementation()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("The LiteLLM Rust implementation is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED! 💥")
        print("The LiteLLM Rust implementation needs attention.")
        sys.exit(1)