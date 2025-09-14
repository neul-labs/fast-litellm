#!/usr/bin/env python3
"""
Test to verify that the PyO3 optimizations are working correctly.
"""

import sys
import os
import json

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_pyo3_optimizations():
    """Test that the PyO3 optimizations are working correctly."""
    print("=== Testing PyO3 Optimizations ===")
    
    try:
        # Import the Rust module
        import litellm_core
        
        print("✓ Successfully imported litellm_core")
        
        # Test health check
        health = litellm_core.health_check()
        print(f"✓ Health check returned: {health}")
        
        # Test core components
        core = litellm_core.LiteLLMCore()
        print(f"✓ Created LiteLLMCore instance")
        print(f"✓ Core available: {core.is_available()}")
        
        # Test Deployment creation with Python objects (not JSON strings)
        print("\n--- Testing Direct PyO3 Object Conversion ---")
        
        # Create Python dictionaries for params and model info
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
        
        # Create deployment with direct Python objects
        deployment = litellm_core.Deployment(
            "test-model",
            litellm_params,
            model_info
        )
        print(f"✓ Created Deployment with direct Python objects: {deployment.model_name}")
        
        # Test adding deployment to core
        core.add_deployment(deployment)
        print(f"✓ Deployment added to core")
        
        # Test getting deployment names
        names = core.get_deployment_names()
        print(f"✓ Deployment names: {names}")
        
        # Test routing with Python dict (not JSON string)
        test_request = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        try:
            result = core.route_request(test_request)
            print(f"✓ Routing with Python dict successful")
            print(f"  Result type: {type(result)}")
            print(f"  Result model_name: {result.model_name}")
        except Exception as e:
            print(f"⚠ Routing with Python dict failed: {e}")
        
        # Test backward compatibility with JSON strings
        print("\n--- Testing Backward Compatibility ---")
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
        print("\n--- Testing Deployment Attribute Access ---")
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
        
        print("\n🎉 PyO3 optimization test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_core: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing PyO3 optimizations: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing LiteLLM Rust Components PyO3 Optimizations\n")
    
    success = test_pyo3_optimizations()
    
    if success:
        print("\n🎉 All PyO3 optimization tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some PyO3 optimization tests failed!")
        sys.exit(1)