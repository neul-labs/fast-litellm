#!/usr/bin/env python3
"""
Simple test to verify that the Rust components compile and can be imported.
"""

import sys
import os

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_basic_compilation():
    """Test that we can import the compiled Rust module."""
    print("=== Testing Basic Rust Module Import ===")
    
    try:
        # Try to import the Rust module
        import litellm_core
        
        print("✓ Successfully imported litellm_core")
        
        # Test health check
        health = litellm_core.health_check()
        print(f"✓ Health check returned: {health}")
        
        # Test core components
        core = litellm_core.LiteLLMCore()
        print(f"✓ Created LiteLLMCore instance")
        print(f"✓ Core available: {core.is_available()}")
        
        print("\n🎉 Basic compilation test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_core: {e}")
        print("This is expected if the module isn't properly built or in the Python path")
        return False
    except Exception as e:
        print(f"✗ Error testing components: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing LiteLLM Rust Components Compilation\n")
    
    success = test_basic_compilation()
    
    if success:
        print("\n🎉 Compilation verification successful!")
        sys.exit(0)
    else:
        print("\n💥 Compilation verification failed!")
        sys.exit(1)