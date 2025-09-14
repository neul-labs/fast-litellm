"""
Test suite for LiteLLM Rust acceleration monkeypatching.
"""
import pytest
from unittest.mock import patch, MagicMock

def test_rust_acceleration_available():
    """Test that Rust acceleration availability is correctly reported."""
    import litellm_rust
    # This should be a boolean
    assert isinstance(litellm_rust.RUST_ACCELERATION_AVAILABLE, bool)

def test_apply_acceleration_function():
    """Test that the apply_acceleration function exists and is callable."""
    from litellm_rust.accelerator import apply_acceleration
    assert callable(apply_acceleration)

def test_remove_acceleration_function():
    """Test that the remove_acceleration function exists and is callable."""
    from litellm_rust.accelerator import remove_acceleration
    assert callable(remove_acceleration)

def test_health_check_function():
    """Test that the health_check function exists and is callable."""
    from litellm_rust.diagnostics import health_check
    assert callable(health_check)

def test_get_performance_stats_function():
    """Test that the get_performance_stats function exists and is callable."""
    from litellm_rust.diagnostics import get_performance_stats
    assert callable(get_performance_stats)

@patch('litellm_rust.rust_extensions.RUST_ACCELERATION_AVAILABLE', True)
def test_apply_acceleration_with_rust_available():
    """Test applying acceleration when Rust components are available."""
    from litellm_rust.accelerator import apply_acceleration
    # This should not raise an exception
    result = apply_acceleration()
    # Result should be a boolean
    assert isinstance(result, bool)

@patch('litellm_rust.rust_extensions.RUST_ACCELERATION_AVAILABLE', False)
def test_apply_acceleration_with_rust_unavailable():
    """Test applying acceleration when Rust components are not available."""
    from litellm_rust.accelerator import apply_acceleration
    # This should not raise an exception
    result = apply_acceleration()
    # Should return False when Rust is not available
    assert result is False

def test_monkeypatch_module_import():
    """Test that the monkeypatch module can be imported."""
    try:
        from litellm_rust import monkeypatch
        assert monkeypatch is not None
    except ImportError:
        pytest.fail("Failed to import monkeypatch module")

def test_auto_apply_acceleration():
    """Test that auto_apply_acceleration function exists."""
    from litellm_rust.monkeypatch import auto_apply_acceleration
    assert callable(auto_apply_acceleration)

if __name__ == "__main__":
    test_rust_acceleration_available()
    test_apply_acceleration_function()
    test_remove_acceleration_function()
    test_health_check_function()
    test_get_performance_stats_function()
    test_apply_acceleration_with_rust_available()
    test_apply_acceleration_with_rust_unavailable()
    test_monkeypatch_module_import()
    test_auto_apply_acceleration()
    print("All tests passed!")