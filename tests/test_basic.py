"""Basic tests for litellm_rust package"""

import pytest


def test_import_package():
    """Test that the package can be imported"""
    try:
        import litellm_rust
        assert hasattr(litellm_rust, '__version__')
        assert hasattr(litellm_rust, 'RUST_ACCELERATION_AVAILABLE')
    except ImportError:
        pytest.skip("Package not built yet")


def test_health_check():
    """Test basic health check functionality"""
    try:
        import litellm_rust
        health = litellm_rust.health_check()
        assert isinstance(health, dict)
        assert 'status' in health
    except ImportError:
        pytest.skip("Package not built yet")


def test_feature_flags():
    """Test feature flag functionality"""
    try:
        import litellm_rust

        # Test getting feature status
        status = litellm_rust.get_feature_status()
        assert isinstance(status, dict)

        # Test checking if a feature is enabled
        enabled = litellm_rust.is_enabled('test_feature')
        assert isinstance(enabled, bool)

    except ImportError:
        pytest.skip("Package not built yet")


def test_performance_monitoring():
    """Test performance monitoring functionality"""
    try:
        import litellm_rust

        # Test recording performance data
        litellm_rust.record_performance(
            component="test",
            operation="test_op",
            duration_ms=10.5,
            success=True
        )

        # Test getting performance stats
        stats = litellm_rust.get_performance_stats()
        assert isinstance(stats, dict)

    except ImportError:
        pytest.skip("Package not built yet")


@pytest.mark.asyncio
async def test_async_compatibility():
    """Test that the package works with async code"""
    try:
        import litellm_rust
        import asyncio

        # Test async health check
        async def async_health_check():
            return litellm_rust.health_check()

        result = await async_health_check()
        assert isinstance(result, dict)

    except ImportError:
        pytest.skip("Package not built yet")