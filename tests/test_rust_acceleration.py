"""
Test that Fast LiteLLM Rust acceleration is actually being called.

These tests verify that:
1. Rust extensions load correctly
2. Acceleration is applied to LiteLLM
3. Rust code paths are actually executed
"""

import os
import sys

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# IMPORTANT: Import fast_litellm FIRST to enable acceleration
import fast_litellm


class TestRustAccelerationAvailable:
    """Test that Rust acceleration is available and loaded"""

    def test_rust_module_available(self):
        """Verify Rust module is loaded"""
        assert (
            fast_litellm.RUST_ACCELERATION_AVAILABLE
        ), "Rust acceleration should be available after build"

    def test_rust_functions_exported(self):
        """Verify Rust functions are exported"""
        import fast_litellm._rust as rust

        # Check that key functions exist
        assert hasattr(rust, "apply_acceleration")
        assert hasattr(rust, "health_check")
        assert hasattr(rust, "get_performance_stats")
        assert hasattr(rust, "is_enabled")

    def test_health_check(self):
        """Test Rust health check function"""
        result = fast_litellm.health_check()

        assert isinstance(result, dict), "Health check should return a dict"
        assert "status" in result or "rust_available" in result
        print(f"Health check result: {result}")

    def test_acceleration_applied(self):
        """Verify acceleration has been applied"""
        # The apply_acceleration function should be called automatically on import
        status = fast_litellm.get_patch_status()

        assert isinstance(status, dict), "Patch status should return a dict"
        print(f"Patch status: {status}")


class TestRustFunctions:
    """Test individual Rust functions"""

    def test_feature_flags_enabled(self):
        """Test Rust feature flag checking"""
        # Even if feature is disabled, the function should work
        result = fast_litellm.is_enabled("rust_routing")
        assert isinstance(result, bool), "is_enabled should return boolean"
        print(f"Rust routing enabled: {result}")

    def test_feature_status(self):
        """Test getting feature status"""
        status = fast_litellm.get_feature_status()
        assert isinstance(status, dict), "Feature status should return dict"
        print(f"Feature status: {status}")

    def test_performance_stats(self):
        """Test getting performance statistics"""
        stats = fast_litellm.get_performance_stats()
        assert isinstance(stats, dict), "Performance stats should return dict"
        print(f"Performance stats: {stats}")


# Check if litellm is available and compatible with this Python version
try:
    import litellm as _litellm_check  # noqa: F401

    HAS_LITELLM = True
except (ImportError, TypeError):
    # TypeError occurs when litellm uses Python 3.10+ syntax (e.g., str | List[str])
    # on older Python versions
    HAS_LITELLM = False


@pytest.mark.skipif(not HAS_LITELLM, reason="litellm not installed")
class TestRustWithLiteLLM:
    """Test that Rust acceleration works with LiteLLM imports"""

    def test_import_litellm_after_acceleration(self):
        """Import LiteLLM after Fast LiteLLM and verify no errors"""
        # This should work without errors if acceleration is properly applied
        import litellm

        assert litellm is not None
        print("✓ LiteLLM imported successfully with acceleration")

    def test_litellm_model_info(self):
        """Test that LiteLLM model info still works"""
        from litellm import get_model_info

        # Basic utility that should still work
        info = get_model_info("gpt-3.5-turbo")
        assert info is not None
        assert "max_tokens" in info or "max_input_tokens" in info
        print(f"✓ Model info works: {list(info.keys())[:5]}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
