#!/usr/bin/env python3
"""
Simple test to verify that the connection pooling components work.
"""

import sys
import os

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "debug"))

def test_basic_compilation():
    """Test that we can import the compiled Rust module."""
    print("=== Testing Basic Connection Pooling Module Import ===")
    
    try:
        # Try to import the Rust module
        import litellm_connection_pool
        
        print("✓ Successfully imported litellm_connection_pool")
        
        # Test health check
        health = litellm_connection_pool.connection_pool_health_check()
        print(f"✓ Health check returned: {health}")
        
        print("\n🎉 Basic compilation test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_connection_pool: {e}")
        print("This is expected if the module isn't properly built or in the Python path")
        return False
    except Exception as e:
        print(f"✗ Error testing components: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing LiteLLM Rust Connection Pooling Components\n")
    
    success = test_basic_compilation()
    
    if success:
        print("\n🎉 Basic compilation verification successful!")
        sys.exit(0)
    else:
        print("\n💥 Basic compilation verification failed!")
        sys.exit(1)