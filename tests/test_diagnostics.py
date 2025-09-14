"""
Test suite for LiteLLM Rust acceleration diagnostics.
"""
import pytest
from unittest.mock import patch, MagicMock

def test_health_check_returns_dict():
    """Test that health_check returns a dictionary."""
    from litellm_rust.diagnostics import health_check
    result = health_check()
    assert isinstance(result, dict)

def test_get_performance_stats_returns_dict():
    """Test that get_performance_stats returns a dictionary."""
    from litellm_rust.diagnostics import get_performance_stats
    result = get_performance_stats()
    assert isinstance(result, dict)

@patch('litellm_rust.rust_extensions.RUST_ACCELERATION_AVAILABLE', True)
def test_health_check_with_rust_available():
    """Test health check when Rust components are available."""
    from litellm_rust.diagnostics import health_check
    result = health_check()
    assert "rust_acceleration_available" in result
    assert result["rust_acceleration_available"] is True

@patch('litellm_rust.rust_extensions.RUST_ACCELERATION_AVAILABLE', False)
def test_health_check_with_rust_unavailable():
    """Test health check when Rust components are not available."""
    from litellm_rust.diagnostics import health_check
    result = health_check()
    assert "rust_acceleration_available" in result
    assert result["rust_acceleration_available"] is False
    assert "error" in result

@patch('litellm_rust.rust_extensions.RUST_ACCELERATION_AVAILABLE', True)
def test_get_performance_stats_with_rust_available():
    """Test performance stats when Rust components are available."""
    from litellm_rust.diagnostics import get_performance_stats
    result = get_performance_stats()
    assert "rust_acceleration_available" in result
    assert result["rust_acceleration_available"] is True

@patch('litellm_rust.rust_extensions.RUST_ACCELERATION_AVAILABLE', False)
def test_get_performance_stats_with_rust_unavailable():
    """Test performance stats when Rust components are not available."""
    from litellm_rust.diagnostics import get_performance_stats
    result = get_performance_stats()
    assert "rust_acceleration_available" in result
    assert result["rust_acceleration_available"] is False
    assert "error" in result

if __name__ == "__main__":
    test_health_check_returns_dict()
    test_get_performance_stats_returns_dict()
    test_health_check_with_rust_available()
    test_health_check_with_rust_unavailable()
    test_get_performance_stats_with_rust_available()
    test_get_performance_stats_with_rust_unavailable()
    print("All tests passed!")