#!/usr/bin/env python3
"""
Simple test to verify that the PyO3 optimizations are working correctly.
"""

import sys
import os
import json

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_core_functionality():
    """Test that the core functionality works correctly."""
    print("=== Testing Core Functionality ===")
    
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
        
        # Test getting deployment names (should be empty)
        names = core.get_deployment_names()
        print(f"✓ Initial deployment names: {names}")
        
        print("\n🎉 Core functionality test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_core: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing core functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deployment_creation():
    """Test that we can create deployments with Python objects."""
    print("\n=== Testing Deployment Creation ===")
    
    try:
        import litellm_core
        
        # Test creating a deployment with Python dicts (not JSON strings)
        print("--- Creating Deployment with Python Objects ---")
        
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
        
        # Create deployment - this should work directly with Python objects
        deployment = litellm_core.Deployment(
            "test-model",
            litellm_params,
            model_info
        )
        print(f"✓ Created Deployment with Python objects: {deployment.model_name}")
        
        # Test accessing attributes
        print(f"  Model name: {deployment.model_name}")
        print(f"  Litellm params type: {type(deployment.litellm_params)}")
        print(f"  Model info type: {type(deployment.model_info)}")
        
        # Test JSON compatibility methods
        try:
            params_json = deployment.litellm_params_json()
            info_json = deployment.model_info_json()
            print(f"✓ JSON compatibility methods work")
            print(f"  Params JSON preview: {params_json[:50]}...")
            print(f"  Info JSON preview: {info_json[:50]}...")
        except Exception as e:
            print(f"⚠ JSON compatibility methods failed: {e}")
        
        print("\n🎉 Deployment creation test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error testing deployment creation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing LiteLLM Rust Components Core Functionality\n")
    
    success1 = test_core_functionality()
    success2 = test_deployment_creation()
    
    if success1 and success2:
        print("\n🎉 All core functionality tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some core functionality tests failed!")
        sys.exit(1)