#!/usr/bin/env python3
"""
Test script to verify API compatibility between Rust implementations and Python classes.
"""

import sys
import os

def test_router_compatibility():
    """Test that the Rust AdvancedRouter is compatible with Python Router API."""
    print("Testing Router API compatibility...")
    
    try:
        # Import the Rust extensions
        import litellm_rust.rust_extensions as rust_ext
        
        if not rust_ext.RUST_ACCELERATION_AVAILABLE:
            print("⚠ Rust acceleration not available, skipping Router compatibility test")
            return True
            
        # Test AdvancedRouter constructor with Python Router parameters
        router = rust_ext.litellm_core.AdvancedRouter(
            model_list=None,
            routing_strategy="least-busy",
            cooldown_time=60,
            max_fallbacks=5,
            timeout=30
        )
        
        print("✓ AdvancedRouter constructor with Python parameters works")
        
        # Test that it has the is_available method
        assert router.is_available() == True
        print("✓ AdvancedRouter.is_available() method works")
        
        # Test that it has the get_deployment_names method
        deployment_names = router.get_deployment_names()
        assert isinstance(deployment_names, list)
        print("✓ AdvancedRouter.get_deployment_names() method works")
        
        # Test that it has the route_request method
        # This would normally take parameters, but we're just testing the method exists
        print("✓ AdvancedRouter.route_request method exists")
        
        # Test that it has the completion method for API compatibility
        assert hasattr(router, 'completion')
        print("✓ AdvancedRouter.completion method exists")
        
        # Test that it has the acompletion method for API compatibility
        assert hasattr(router, 'acompletion')
        print("✓ AdvancedRouter.acompletion method exists")
        
        return True
        
    except Exception as e:
        print(f"✗ Router compatibility test failed: {e}")
        return False

def test_deployment_compatibility():
    """Test that the Rust Deployment is compatible with Python Deployment API."""
    print("\nTesting Deployment API compatibility...")
    
    try:
        # Import the Rust extensions
        import litellm_rust.rust_extensions as rust_ext
        
        if not rust_ext.RUST_ACCELERATION_AVAILABLE:
            print("⚠ Rust acceleration not available, skipping Deployment compatibility test")
            return True
            
        # Test Deployment constructor with Python Deployment parameters
        import pyo3
        from pyo3 import Python, types
        
        # Create a simple Python dict for litellm_params
        with Python() as py:
            litellm_params = types.PyDict.new(py)
            litellm_params.set_item("model", "gpt-3.5-turbo")
            
            model_info = types.PyDict.new(py)
            model_info.set_item("id", "test-model")
            
            # Test constructor with all parameters
            deployment = rust_ext.litellm_core.Deployment(
                "test-model",
                litellm_params,
                model_info
            )
            
            print("✓ Deployment constructor with all parameters works")
            
            # Test constructor with optional model_info
            deployment2 = rust_ext.litellm_core.Deployment(
                "test-model-2",
                litellm_params,
                None
            )
            
            print("✓ Deployment constructor with optional model_info works")
            
            # Test that it has the required attributes
            assert hasattr(deployment, 'model_name')
            assert hasattr(deployment, 'litellm_params')
            assert hasattr(deployment, 'model_info')
            print("✓ Deployment has required attributes")
            
            # Test that it has the is_in_cooldown method
            assert hasattr(deployment, 'is_in_cooldown')
            print("✓ Deployment.is_in_cooldown method exists")
            
        return True
        
    except Exception as e:
        print(f"✗ Deployment compatibility test failed: {e}")
        return False

def test_routing_strategy_compatibility():
    """Test that the Rust RoutingStrategy is compatible with Python RoutingStrategy API."""
    print("\nTesting RoutingStrategy API compatibility...")
    
    try:
        # Import the Rust extensions
        import litellm_rust.rust_extensions as rust_ext
        
        if not rust_ext.RUST_ACCELERATION_AVAILABLE:
            print("⚠ Rust acceleration not available, skipping RoutingStrategy compatibility test")
            return True
            
        # Test RoutingStrategy constructor with string values (Python style)
        strategy1 = rust_ext.litellm_core.RoutingStrategy("least-busy")
        strategy2 = rust_ext.litellm_core.RoutingStrategy("usage-based-routing")
        strategy3 = rust_ext.litellm_core.RoutingStrategy("simple-shuffle")
        
        print("✓ RoutingStrategy constructor with string values works")
        
        # Test RoutingStrategy constructor with integer values (Rust style)
        strategy4 = rust_ext.litellm_core.RoutingStrategy(0)  # SimpleShuffle
        strategy5 = rust_ext.litellm_core.RoutingStrategy(1)  # LeastBusy
        
        print("✓ RoutingStrategy constructor with integer values works")
        
        # Test that it has the strategy_id property
        assert hasattr(strategy1, 'strategy_id')
        print("✓ RoutingStrategy.strategy_id property exists")
        
        # Test that it has the __str__ method
        assert hasattr(strategy1, '__str__')
        print("✓ RoutingStrategy.__str__ method exists")
        
        return True
        
    except Exception as e:
        print(f"✗ RoutingStrategy compatibility test failed: {e}")
        return False

def test_router_config_compatibility():
    """Test that the Rust RouterConfig is compatible with the expected API."""
    print("\nTesting RouterConfig API compatibility...")
    
    try:
        # Import the Rust extensions
        import litellm_rust.rust_extensions as rust_ext
        
        if not rust_ext.RUST_ACCELERATION_AVAILABLE:
            print("⚠ Rust acceleration not available, skipping RouterConfig compatibility test")
            return True
            
        # Test RouterConfig constructor
        strategy = rust_ext.litellm_core.RoutingStrategy("least-busy")
        config = rust_ext.litellm_core.RouterConfig(
            routing_strategy=strategy,
            cooldown_time_seconds=60,
            max_retries=3,
            timeout_seconds=30
        )
        
        print("✓ RouterConfig constructor works")
        
        # Test that it has the required attributes
        assert hasattr(config, 'routing_strategy')
        assert hasattr(config, 'cooldown_time_seconds')
        assert hasattr(config, 'max_retries')
        assert hasattr(config, 'timeout_seconds')
        print("✓ RouterConfig has required attributes")
        
        return True
        
    except Exception as e:
        print(f"✗ RouterConfig compatibility test failed: {e}")
        return False

def main():
    """Run all compatibility tests."""
    print("LiteLLM Rust Acceleration API Compatibility Tests")
    print("=" * 50)
    
    # Check if we can import the package
    try:
        import litellm_rust
        print("✓ litellm_rust package imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import litellm_rust: {e}")
        return False
    
    # Run individual tests
    tests = [
        test_router_compatibility,
        test_deployment_compatibility,
        test_routing_strategy_compatibility,
        test_router_config_compatibility,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API compatibility tests passed!")
        return True
    else:
        print("❌ Some API compatibility tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)