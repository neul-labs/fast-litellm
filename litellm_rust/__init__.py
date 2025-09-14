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
    from . import litellm_core
    from . import litellm_token
    from . import litellm_connection_pool
    from . import litellm_rate_limiter
    
    # Mark that Rust acceleration is available
    RUST_ACCELERATION_AVAILABLE = True
except ImportError as e:
    # If Rust extensions are not available, mark as unavailable
    print(f"Warning: Could not import Rust extensions: {e}")
    RUST_ACCELERATION_AVAILABLE = False

# Import the monkeypatching module
from . import monkeypatch

# Import accelerator control functions
from .accelerator import apply_acceleration, remove_acceleration

# Import diagnostics functions
from .diagnostics import health_check, get_performance_stats

__all__ = [
    "RUST_ACCELERATION_AVAILABLE",
    "apply_acceleration", 
    "remove_acceleration",
    "health_check",
    "get_performance_stats",
    "__version__",
]

# Apply acceleration automatically when the module is imported
if RUST_ACCELERATION_AVAILABLE:
    apply_acceleration()
else:
    print("Rust acceleration is not available. Install with Rust components for better performance.")