"""
LiteLLM Rust Acceleration
=========================

High-performance Rust acceleration for LiteLLM components.

This package provides accelerated implementations of performance-critical
LiteLLM components using Rust and PyO3.

Features:
- Advanced routing with multiple strategies
- Fast token counting using tiktoken-rs
- Efficient rate limiting
- Connection pooling
- Drop-in replacement for existing Python implementations
"""

__version__ = "0.1.0"

# Import key components
try:
    # Try to import the Rust extensions
    from ._rust import *

    # Mark that Rust acceleration is available
    RUST_ACCELERATION_AVAILABLE = True
except ImportError as e:
    # If Rust extensions are not available, mark as unavailable
    print(f"Warning: Could not import Rust extensions: {e}")
    RUST_ACCELERATION_AVAILABLE = False

# Import enhanced systems (fallback to Python-only if Rust not available)
if not RUST_ACCELERATION_AVAILABLE:
    from . import enhanced_monkeypatch
    from . import feature_flags as py_feature_flags
    from . import performance_monitor as py_performance_monitor
    from . import diagnostics

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
        # Apply acceleration using the imported functions
        apply_acceleration()
        print("✅ LiteLLM Rust acceleration enabled")
    except Exception as e:
        print(f"Warning: Failed to apply enhanced acceleration: {e}")
else:
    print("Rust acceleration is not available. Install with Rust components for better performance.")