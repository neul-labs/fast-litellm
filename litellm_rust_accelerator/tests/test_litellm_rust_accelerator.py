"""
Tests for the LiteLLM Rust Accelerator package.
"""

import unittest
import sys
import os

# Add the src directory to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

class TestLiteLLMRustAccelerator(unittest.TestCase):
    """Test cases for the LiteLLM Rust Accelerator package."""
    
    def test_import_package(self):
        """Test that the package can be imported."""
        try:
            import litellm_rust_accelerator
            self.assertTrue(True)
        except ImportError:
            self.fail("Failed to import litellm_rust_accelerator")
    
    def test_create_components(self):
        """Test that components can be created."""
        import litellm_rust_accelerator
        
        # Test core components
        core = litellm_rust_accelerator.LiteLLMCore()
        self.assertIsInstance(core, litellm_rust_accelerator.LiteLLMCore)
        
        # Test token counter
        token_counter = litellm_rust_accelerator.SimpleTokenCounter(100)
        self.assertIsInstance(token_counter, litellm_rust_accelerator.SimpleTokenCounter)
        self.assertEqual(token_counter.cache_size, 100)
        
        # Test rate limiter
        rate_limiter = litellm_rust_accelerator.SimpleRateLimiter()
        self.assertIsInstance(rate_limiter, litellm_rust_accelerator.SimpleRateLimiter)
        
        # Test connection pool
        connection_pool = litellm_rust_accelerator.SimpleConnectionPool(10)
        self.assertIsInstance(connection_pool, litellm_rust_accelerator.SimpleConnectionPool)
        self.assertEqual(connection_pool.max_connections_per_provider, 10)
        
        # Test deployment
        litellm_params = {"model": "gpt-3.5-turbo"}
        model_info = {"description": "Test model"}
        deployment = litellm_rust_accelerator.Deployment(
            "test-model",
            litellm_params,
            model_info
        )
        self.assertIsInstance(deployment, litellm_rust_accelerator.Deployment)
        self.assertEqual(deployment.model_name, "test-model")
    
    def test_token_counting(self):
        """Test token counting functionality."""
        import litellm_rust_accelerator
        
        token_counter = litellm_rust_accelerator.SimpleTokenCounter(100)
        
        # Test basic token counting
        text = "Hello, world!"
        model = "gpt-3.5-turbo"
        token_count = token_counter.count_tokens(text, model)
        self.assertIsInstance(token_count, int)
        self.assertGreater(token_count, 0)
        
        # Test batch token counting
        texts = ["Hello", "world", "test"]
        batch_counts = token_counter.count_tokens_batch(texts, model)
        self.assertIsInstance(batch_counts, list)
        self.assertEqual(len(batch_counts), len(texts))
        self.assertTrue(all(isinstance(count, int) for count in batch_counts))
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        import litellm_rust_accelerator
        
        rate_limiter = litellm_rust_accelerator.SimpleRateLimiter()
        
        # Test rate limit check
        key = "test-user"
        within_limit = rate_limiter.check_rate_limit(key, 100, 60)
        self.assertIsInstance(within_limit, bool)
        
        # Test token consumption
        consumed = rate_limiter.consume_tokens(key, 5)
        self.assertIsInstance(consumed, bool)
        
        # Test rate limit statistics
        stats = rate_limiter.get_rate_limit_stats()
        self.assertIsInstance(stats, dict)
    
    def test_connection_pooling(self):
        """Test connection pooling functionality."""
        import litellm_rust_accelerator
        
        connection_pool = litellm_rust_accelerator.SimpleConnectionPool(10)
        
        # Test getting connection
        provider = "openai"
        conn_id = connection_pool.get_connection(provider)
        self.assertIsInstance(conn_id, str)
        self.assertIn(provider, conn_id)
        
        # Test returning connection
        returned = connection_pool.return_connection(conn_id)
        self.assertIsInstance(returned, bool)
        
        # Test pool statistics
        stats = connection_pool.get_pool_stats()
        self.assertIsInstance(stats, dict)
    
    def test_enable_disable_acceleration(self):
        """Test enabling/disabling Rust acceleration."""
        import litellm_rust_accelerator
        
        # Test enabling acceleration
        result = litellm_rust_accelerator.enable_rust_acceleration(True)
        self.assertIsInstance(result, bool)
        
        # Test disabling acceleration
        result = litellm_rust_accelerator.enable_rust_acceleration(False)
        self.assertIsInstance(result, bool)
        
        # Test checking availability
        available = litellm_rust_accelerator.is_rust_acceleration_available()
        self.assertIsInstance(available, bool)
    
    def test_routing_strategies(self):
        """Test routing strategies enumeration."""
        import litellm_rust_accelerator
        
        # Test that routing strategies are available
        strategies = [
            litellm_rust_accelerator.RoutingStrategy.SimpleShuffle,
            litellm_rust_accelerator.RoutingStrategy.LeastBusy,
            litellm_rust_accelerator.RoutingStrategy.LatencyBased,
            litellm_rust_accelerator.RoutingStrategy.CostBased,
            litellm_rust_accelerator.RoutingStrategy.UsageBasedV1,
            litellm_rust_accelerator.RoutingStrategy.UsageBasedV2,
            litellm_rust_accelerator.RoutingStrategy.LeastBusyWithPenalty,
        ]
        
        self.assertTrue(len(strategies) > 0)

if __name__ == "__main__":
    unittest.main()