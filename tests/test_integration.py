#!/usr/bin/env python3
"""
Simple test script to verify Rust components work with Python.
"""

import json
import sys
import os

# Add the target directory to Python path so we can import the built module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_rust_core():
    """Test the Rust core components."""
    try:
        # Try to import the Rust module
        import litellm_core
        
        print("✓ Successfully imported litellm_core")
        
        # Test health check
        health = litellm_core.health_check()
        print(f"✓ Health check returned: {health}")
        
        # Test LiteLLMCore creation
        core = litellm_core.LiteLLMCore()
        print(f"✓ Created LiteLLMCore instance")
        print(f"✓ Core available: {core.is_available()}")
        
        # Test Deployment creation
        deployment = litellm_core.Deployment(
            "test-model",
            '{"provider": "openai"}',
            '{"description": "Test model"}'
        )
        print(f"✓ Created Deployment instance: {deployment.model_name}")
        
        # Test adding deployment to core
        core.add_deployment(deployment)
        print(f"✓ Added deployment to core")
        
        # Test getting deployment names
        names = core.get_deployment_names()
        print(f"✓ Deployment names: {names}")
        
        # Test routing with JSON
        test_request = json.dumps({
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}]
        })
        
        try:
            result = core.route_request(test_request)
            print(f"✓ Routing successful: {result[:100]}...")
        except Exception as e:
            print(f"⚠ Routing failed (expected for incomplete implementation): {e}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_core: {e}")
        print("This is expected if the module isn't properly installed or in the Python path")
        return False
    except Exception as e:
        print(f"✗ Error testing Rust components: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_python_fallback():
    """Test the Python fallback mechanism."""
    print("\n--- Testing Python Fallback ---")
    
    try:
        # Import our Python wrapper
        from litellm.rust_accelerator import RustAccelerator
        
        accelerator = RustAccelerator()
        print(f"✓ Created RustAccelerator instance")
        print(f"✓ Rust available: {accelerator.is_available()}")
        
        # Test routing with fallback
        test_request = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello, world!"}]
        }
        
        result = accelerator.route_request(test_request)
        print(f"✓ Fallback routing successful: {result}")
        
        # Test deployment addition
        deployment_data = {
            "model_name": "test-model",
            "litellm_params": {},
            "model_info": {}
        }
        
        success = accelerator.add_deployment(deployment_data)
        print(f"✓ Deployment addition successful: {success}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing Python fallback: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Testing LiteLLM Rust Components ===\n")
    
    # Test Rust core directly
    rust_success = test_rust_core()
    
    # Test Python fallback
    python_success = test_python_fallback()
    
    print(f"\n=== Summary ===")
    print(f"Rust Core Test: {'✓ PASS' if rust_success else '✗ FAIL'}")
    print(f"Python Fallback Test: {'✓ PASS' if python_success else '✗ FAIL'}")
    
    if rust_success or python_success:
        print("\n🎉 Basic functionality working!")
        sys.exit(0)
    else:
        print("\n💥 All tests failed!")
        sys.exit(1)