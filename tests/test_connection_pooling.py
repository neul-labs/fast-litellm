#!/usr/bin/env python3
"""
Test script for connection pooling functionality.
"""

import sys
import os

# Add the target directory to Python path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "target", "release"))

def test_connection_pooling():
    """Test that the connection pooling functionality works correctly."""
    print("=== Testing Connection Pooling Functionality ===")
    
    try:
        # Import the Rust module
        import litellm_connection_pool
        
        print("✓ Successfully imported litellm_connection_pool")
        
        # Test health check
        health = litellm_connection_pool.connection_pool_health_check()
        print(f"✓ Health check returned: {health}")
        
        # Test connection pool creation
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
        
        print("\n🎉 Connection pooling test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import litellm_connection_pool: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing connection pooling: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing LiteLLM Rust Connection Pooling Components\n")
    
    success = test_connection_pooling()
    
    if success:
        print("\n🎉 All connection pooling tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Connection pooling tests failed!")
        sys.exit(1)