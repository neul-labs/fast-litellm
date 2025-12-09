"""
Health check and diagnostics for Fast LiteLLM Rust acceleration.
"""

from typing import Any, Dict


def health_check() -> Dict[str, Any]:
    """
    Perform a comprehensive health check of all Rust components.

    Returns:
        Dict[str, Any]: Health check results
    """
    try:
        from fast_litellm import _rust

        rust_available = True
    except ImportError:
        rust_available = False

    results = {"rust_acceleration_available": rust_available, "components": {}}

    if not rust_available:
        results["error"] = "Rust acceleration is not available"
        results["message"] = "Install from source with maturin for full acceleration"
        return results

    # Check if health_check function exists in Rust module
    if hasattr(_rust, "health_check"):
        try:
            rust_health = _rust.health_check()
            results["components"]["rust"] = rust_health
            results["overall_healthy"] = rust_health.get("status") == "ok"
        except Exception as e:
            results["components"]["rust"] = {"error": str(e)}
            results["overall_healthy"] = False
    else:
        results["components"]["rust"] = {
            "status": "available",
            "health_check": "not_implemented",
        }
        results["overall_healthy"] = True

    return results


def get_performance_stats() -> Dict[str, Any]:
    """
    Get performance statistics from all Rust components.

    Returns:
        Dict[str, Any]: Performance statistics
    """
    try:
        from fast_litellm import _rust

        rust_available = True
    except ImportError:
        rust_available = False

    stats = {"rust_acceleration_available": rust_available, "components": {}}

    if not rust_available:
        stats["error"] = "Rust acceleration is not available"
        return stats

    # Get stats if available
    if hasattr(_rust, "get_performance_stats"):
        try:
            stats["components"]["rust"] = _rust.get_performance_stats()
        except Exception as e:
            stats["components"]["rust"] = {"error": str(e)}
    else:
        stats["components"]["rust"] = {
            "message": "Performance stats not yet implemented"
        }

    return stats


def get_version_info() -> Dict[str, Any]:
    """
    Get version information for Fast LiteLLM components.

    Returns:
        Dict[str, Any]: Version information
    """
    try:
        import fast_litellm

        version = fast_litellm.__version__
    except Exception:
        version = "unknown"

    try:
        from fast_litellm import _rust

        rust_version = getattr(_rust, "__version__", "0.1.0")
        rust_available = True
    except ImportError:
        rust_version = "not installed"
        rust_available = False

    return {
        "fast_litellm_version": version,
        "rust_module_version": rust_version,
        "rust_available": rust_available,
    }
