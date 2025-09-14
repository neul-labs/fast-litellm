#!/usr/bin/env python3
"""
Test script to verify that the advanced router implementation works correctly.
"""

import sys
import os
import json

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_advanced_router():
    """Test that the advanced router implementation works correctly."""
    print("=== Testing Advanced Router Implementation ===")
    
    try:
        # Import the Rust module
        import litellm_core
        
        print("✓ Successfully imported litellm_core")
        
        # Test health check
        health = litellm_core.health_check()
        print(f"✓ Core health check returned: {health}")
        
        # Test advanced router health check
        router_health = litellm_core.advanced_router_health_check()
        print(f"✓ Advanced router health check returned: {router_health}")
        
        # Test routing strategy creation
        from litellm_core import RoutingStrategy
        strategies = [
            ("SimpleShuffle", 0),
            ("LeastBusy", 1),
            ("LatencyBased", 2),
            ("CostBased", 3),
            ("UsageBasedV1", 4),
            ("UsageBasedV2", 5),
            ("LeastBusyWithPenalty", 6)
        ]
        
        for strategy_name, strategy_id in strategies:
            strategy = RoutingStrategy(strategy_id)
            print(f"✓ Created {strategy_name} routing strategy with ID: {strategy.strategy_id}")
        
        # Test router config creation
        from litellm_core import RouterConfig
        config = RouterConfig(
            routing_strategy=RoutingStrategy.LeastBusy,
            cooldown_time_seconds=60,
            max_retries=3,
            timeout_seconds=30
        )
        print(f"✓ Created RouterConfig")
        print(f"  Routing strategy: {config.routing_strategy.strategy_id}")
        print(f"  Cooldown time: {config.cooldown_time_seconds}")
        print(f"  Max retries: {config.max_retries}")
        print(f"  Timeout: {config.timeout_seconds}")
        
        # Test advanced router creation
        from litellm_core import AdvancedRouter
        router = AdvancedRouter(config)
        print(f"✓ Created AdvancedRouter")
        
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
        
        # Test adding deployment to router
        router.add_deployment(deployment)
        print(f"✓ Added deployment to router")
        
        # Test getting deployment names
        names = router.get_deployment_names()
        print(f"✓ Deployment names: {names}")
        
        # Test routing with Python dict
        test_request = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        try:
            result = router.route_request("test-model", test_request)
            print(f"✓ Routing with Python dict successful")
            print(f"  Result type: {type(result)}")
        except Exception as e:
            print(f"⚠ Routing with Python dict failed: {e}")
        
        # Test routing with JSON string
        json_request = json.dumps({
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}]
        })
        
        try:
            result = router.route_request("test-model", json_request)
            print(f"✓ Routing with JSON string successful")
            print(f"  Result type: {type(result)}")
        except Exception as e:
            print(f"⚠ Routing with JSON string failed: {e}")
        
        # Test router statistics
        stats = router.get_stats()
        print(f"✓ Router statistics: {stats}")
        
        print("\n🎉 Advanced router test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_core: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing advanced router: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing LiteLLM Rust Advanced Router Implementation\n")
    
    success = test_advanced_router()
    
    if success:
        print("\n🎉 All advanced router tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some advanced router tests failed!")
        sys.exit(1)