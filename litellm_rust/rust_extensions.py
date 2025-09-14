import sys
import os

# Add the directory containing the Rust extensions to the Python path
rust_lib_dir = os.path.join(os.path.dirname(__file__), "rust_extensions")
if os.path.exists(rust_lib_dir) and rust_lib_dir not in sys.path:
    sys.path.insert(0, rust_lib_dir)

# Import the Rust extensions
try:
    import litellm_core
    import litellm_token
    import litellm_connection_pool
    import litellm_rate_limiter
    
    # Mark that Rust acceleration is available
    RUST_ACCELERATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Rust extensions: {e}")
    RUST_ACCELERATION_AVAILABLE = False

__all__ = [
    "RUST_ACCELERATION_AVAILABLE",
    "litellm_core",
    "litellm_token",
    "litellm_connection_pool",
    "litellm_rate_limiter",
]