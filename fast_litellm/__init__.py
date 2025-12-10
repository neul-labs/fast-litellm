"""
Fast LiteLLM
============

High-performance Rust acceleration for LiteLLM.

This package provides drop-in acceleration for performance-critical LiteLLM
operations using Rust and PyO3.

Performance (vs production-grade Python with thread-safety):
- 3.2x faster connection pooling (DashMap lock-free)
- 1.6x faster rate limiting (atomic operations)
- 1.5-1.7x faster large text tokenization (tiktoken-rs)
- 42x more memory efficient for high-cardinality rate limiting
- Zero configuration - just import before litellm
- Production-safe with automatic fallback

Example:
    >>> import fast_litellm  # Enables acceleration
    >>> import litellm
    >>> # All LiteLLM operations now use Rust acceleration
"""

__version__ = "0.1.0"

# Import key components
import warnings

try:
    # Try to import the Rust extensions
    from ._rust import *

    # Mark that Rust acceleration is available
    RUST_ACCELERATION_AVAILABLE = True
except ImportError as e:
    # If Rust extensions are not available, mark as unavailable
    warnings.warn(
        f"Fast LiteLLM: Rust extensions not available ({e}). "
        "Falling back to Python implementations. "
        "Install from source with 'pip install fast-litellm --no-binary :all:' for full acceleration.",
        ImportWarning,
        stacklevel=2,
    )
    RUST_ACCELERATION_AVAILABLE = False

# Import enhanced systems (fallback to Python-only if Rust not available)
if not RUST_ACCELERATION_AVAILABLE:
    from . import diagnostics, enhanced_monkeypatch
    from . import feature_flags as py_feature_flags
    from . import performance_monitor as py_performance_monitor

    # Use Python implementations as fallbacks
    apply_acceleration = enhanced_monkeypatch.enhanced_apply_acceleration
    remove_acceleration = enhanced_monkeypatch.remove_enhanced_acceleration
    get_patch_status = enhanced_monkeypatch.get_patch_status
    is_enabled = py_feature_flags.is_enabled
    get_feature_status = py_feature_flags.get_status
    reset_errors = py_feature_flags.reset_errors
    record_performance = py_performance_monitor.record_performance
    get_performance_stats = py_performance_monitor.get_stats
    compare_implementations = py_performance_monitor.compare_implementations
    get_recommendations = py_performance_monitor.get_recommendations
    export_performance_data = py_performance_monitor.export_performance_data
    health_check = diagnostics.health_check

__all__ = [
    "RUST_ACCELERATION_AVAILABLE",
    "apply_acceleration",
    "remove_acceleration",
    "health_check",
    "get_performance_stats",
    "get_patch_status",
    "is_enabled",
    "get_feature_status",
    "reset_errors",
    "record_performance",
    "compare_implementations",
    "get_recommendations",
    "export_performance_data",
    "__version__",
]

# Apply enhanced acceleration automatically when the module is imported
if RUST_ACCELERATION_AVAILABLE:
    try:
        # Import and apply enhanced acceleration (actual monkeypatching)
        from . import _rust, enhanced_monkeypatch

        # Create a mock module structure that enhanced_apply_acceleration expects
        class _RustModule:
            RUST_ACCELERATION_AVAILABLE = True

        rust_module = _RustModule()
        rust_module.fast_litellm = _rust
        rust_module._rust = _rust

        enhanced_monkeypatch.enhanced_apply_acceleration(rust_module)
    except Exception as e:
        warnings.warn(
            f"Fast LiteLLM: Failed to apply acceleration: {e}",
            RuntimeWarning,
            stacklevel=2,
        )
