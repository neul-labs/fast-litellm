#!/usr/bin/env python3
"""
Test script to verify that the package structure is correct and can be imported.
"""

def test_package_import():
    """Test that the package can be imported."""
    try:
        import litellm_rust
        print("✓ litellm_rust package imported successfully")
        print(f"  Version: {litellm_rust.__version__}")
        print(f"  Rust acceleration available: {litellm_rust.RUST_ACCELERATION_AVAILABLE}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import litellm_rust: {e}")
        return False

def test_package_components():
    """Test that package components can be accessed."""
    try:
        import litellm_rust
        
        # Test that key functions are available
        assert hasattr(litellm_rust, 'apply_acceleration')
        assert hasattr(litellm_rust, 'remove_acceleration')
        assert hasattr(litellm_rust, 'health_check')
        assert hasattr(litellm_rust, 'get_performance_stats')
        
        print("✓ All package components are accessible")
        return True
    except (ImportError, AssertionError) as e:
        print(f"✗ Failed to access package components: {e}")
        return False

def test_rust_extensions():
    """Test that Rust extensions can be imported."""
    try:
        import litellm_rust
        
        if litellm_rust.RUST_ACCELERATION_AVAILABLE:
            # Try to import the Rust extensions directly
            from litellm_rust import litellm_core
            from litellm_rust import litellm_token
            from litellm_rust import litellm_connection_pool
            from litellm_rust import litellm_rate_limiter
            
            print("✓ All Rust extensions imported successfully")
            return True
        else:
            print("ℹ Rust acceleration not available, skipping extension tests")
            return True
    except ImportError as e:
        print(f"✗ Failed to import Rust extensions: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing LiteLLM Rust Acceleration Package Structure")
    print("=" * 55)
    
    tests = [
        test_package_import,
        test_package_components,
        test_rust_extensions,
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
        print("🎉 All package structure tests passed!")
        return True
    else:
        print("❌ Some package structure tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)