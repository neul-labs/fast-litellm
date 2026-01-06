"""
Enhanced monkeypatching with feature flags and performance monitoring.

This module provides an advanced monkeypatching system that integrates with
the feature flag system for safe, gradual rollout of Rust acceleration.
"""

import asyncio
import functools
import importlib
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict

from .feature_flags import FeatureState, is_enabled, record_error, record_performance

logger = logging.getLogger(__name__)

# Store references to original classes and functions
_original_implementations: Dict[str, Any] = {}
_rust_implementations: Dict[str, Any] = {}
_patched_functions: Dict[str, str] = {}  # Maps function -> feature flag name
_feature_modes: Dict[str, str] = {}  # Cached feature modes for fast paths


class PerformanceWrapper:
    """
    Wrapper that measures performance and handles fallback with optimized paths.

    This wrapper determines the optimal execution mode at initialization time:
    - rust_direct: Always use Rust implementation (no feature flag checks)
    - python_only: Always use Python implementation (Rust disabled)
    - conditional: Check feature flags per call (for gradual rollouts)

    The mode is determined once at wrapper creation, avoiding per-call overhead
    for stable features that are fully enabled or disabled.

    Attributes:
        original_func: The original Python function
        rust_func: The Rust-accelerated function
        feature_name: Feature flag name for this wrapper
        _mode: Determined execution mode (rust_direct, python_only, or conditional)
    """

    __slots__ = ('original_func', 'rust_func', 'feature_name', '_mode', '__name__', '__annotations__', '__wrapped__')

    def __init__(self, original_func: Callable, rust_func: Callable, feature_name: str):
        self.original_func = original_func
        self.rust_func = rust_func
        self.feature_name = feature_name
        self.__wrapped__ = original_func

        # Manually copy wrapper attributes (some may be read-only)
        try:
            if hasattr(original_func, '__name__'):
                self.__name__ = original_func.__name__
        except (AttributeError, TypeError):
            pass

        # __doc__ is handled at class level, not in __slots__
        try:
            if hasattr(original_func, '__doc__'):
                object.__setattr__(self, '__doc__', original_func.__doc__)
        except (AttributeError, TypeError):
            pass

        try:
            if hasattr(original_func, '__annotations__'):
                self.__annotations__ = original_func.__annotations__
        except (AttributeError, TypeError):
            pass

        # Determine the optimization mode at initialization
        # This avoids per-call feature flag checks for stable features
        self._mode = self._determine_mode()

        # Log mode detection for debugging
        logger.debug(
            f"PerformanceWrapper initialized for '{feature_name}': "
            f"mode={self._mode}"
        )

    def _determine_mode(self) -> str:
        """
        Determine the optimal execution mode based on feature flag state.

        Returns:
            One of: 'rust_direct', 'python_only', or 'conditional'
        """
        try:
            from .feature_flags import _feature_manager
            if _feature_manager is not None:
                feature = _feature_manager._features.get(self.feature_name)
                if feature is not None:
                    if feature.state == FeatureState.ENABLED:
                        return "rust_direct"  # Skip all checks, go straight to Rust
                    elif feature.state == FeatureState.DISABLED:
                        return "python_only"  # Never use Rust
        except Exception:
            pass
        return "conditional"  # Default: check feature flags per call

    def __call__(self, *args, **kwargs):
        """Execute with performance monitoring and fallback."""
        mode = self._mode

        # Fast path: Always use Rust
        if mode == "rust_direct":
            return self._call_rust_fast(*args, **kwargs)

        # Fast path: Always use Python
        if mode == "python_only":
            return self.original_func(*args, **kwargs)

        # Conditional path: Check feature flags
        return self._call_conditional(*args, **kwargs)

    def _call_rust_fast(self, *args, **kwargs):
        """Direct Rust call with minimal overhead for always-enabled features."""
        try:
            return self.rust_func(*args, **kwargs)
        except Exception as e:
            record_error(self.feature_name, e)
            return self.original_func(*args, **kwargs)

    def _call_conditional(self, *args, **kwargs):
        """Conditional call with feature flag checking."""
        # Extract request_id with minimal overhead
        request_id = kwargs.get("request_id")
        if not request_id and args:
            try:
                request_id = getattr(args[0], "request_id", None)
            except (IndexError, AttributeError):
                request_id = None

        if not is_enabled(self.feature_name, request_id):
            return self.original_func(*args, **kwargs)

        start_time = time.perf_counter()
        try:
            result = self.rust_func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000
            record_performance(self.feature_name, duration_ms)
            return result

        except Exception as e:
            record_error(self.feature_name, e)
            try:
                return self.original_func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(
                    f"Both Rust and Python implementations failed for {self.feature_name}: {fallback_error}"
                )
                raise

    def __get__(self, instance, owner):
        """Support for bound methods."""
        if instance is None:
            return self
        return functools.partial(self.__call__, instance)


class AsyncPerformanceWrapper:
    """
    Async wrapper with same optimizations as PerformanceWrapper.

    This wrapper handles async functions with the same three-mode optimization:
    - rust_direct: Always use Rust implementation
    - python_only: Always use Python implementation
    - conditional: Check feature flags per call

    See PerformanceWrapper for mode details.
    """

    __slots__ = ('original_func', 'rust_func', 'feature_name', '_mode', '__name__', '__wrapped__')

    def __init__(self, original_func: Callable, rust_func: Callable, feature_name: str):
        self.original_func = original_func
        self.rust_func = rust_func
        self.feature_name = feature_name
        self.__wrapped__ = original_func

        # Manually copy wrapper attributes
        try:
            if hasattr(original_func, '__name__'):
                self.__name__ = original_func.__name__
        except (AttributeError, TypeError):
            pass

        # __doc__ is handled at class level
        try:
            if hasattr(original_func, '__doc__'):
                object.__setattr__(self, '__doc__', original_func.__doc__)
        except (AttributeError, TypeError):
            pass

        self._mode = self._determine_mode()

        # Log mode detection for debugging
        logger.debug(
            f"AsyncPerformanceWrapper initialized for '{feature_name}': "
            f"mode={self._mode}"
        )

    def _determine_mode(self) -> str:
        """
        Determine the optimal execution mode based on feature flag state.

        Returns:
            One of: 'rust_direct', 'python_only', or 'conditional'
        """
        try:
            from .feature_flags import _feature_manager
            if _feature_manager is not None:
                feature = _feature_manager._features.get(self.feature_name)
                if feature is not None:
                    if feature.state == FeatureState.ENABLED:
                        return "rust_direct"
                    elif feature.state == FeatureState.DISABLED:
                        return "python_only"
        except Exception:
            pass
        return "conditional"

    async def __call__(self, *args, **kwargs):
        """Execute async with performance monitoring and fallback."""
        mode = self._mode

        if mode == "rust_direct":
            return await self._call_rust_fast(*args, **kwargs)

        if mode == "python_only":
            return await self.original_func(*args, **kwargs)

        return await self._call_conditional(*args, **kwargs)

    async def _call_rust_fast(self, *args, **kwargs):
        """Direct async Rust call."""
        try:
            return await self.rust_func(*args, **kwargs)
        except Exception as e:
            record_error(self.feature_name, e)
            return await self.original_func(*args, **kwargs)

    async def _call_conditional(self, *args, **kwargs):
        """Conditional async call."""
        request_id = kwargs.get("request_id")
        if not request_id and args:
            try:
                request_id = getattr(args[0], "request_id", None)
            except (IndexError, AttributeError):
                request_id = None

        if not is_enabled(self.feature_name, request_id):
            return await self.original_func(*args, **kwargs)

        start_time = time.perf_counter()
        try:
            result = await self.rust_func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000
            record_performance(self.feature_name, duration_ms)
            return result

        except Exception as e:
            record_error(self.feature_name, e)
            try:
                return await self.original_func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(
                    f"Both Rust and Python implementations failed for {self.feature_name}: {fallback_error}"
                )
                raise


def enhanced_patch_function(
    module_name: str, function_name: str, rust_function: Any, feature_name: str
) -> bool:
    """
    Enhanced function patching with feature flags and performance monitoring.

    Args:
        module_name: Name of the module containing the function
        function_name: Name of the function to patch
        rust_function: Rust implementation to use
        feature_name: Feature flag name for this patch

    Returns:
        bool: True if patching was successful, False otherwise
    """
    try:
        # Import the module
        module = importlib.import_module(module_name)

        # Store the original function if it exists
        if hasattr(module, function_name):
            original_function = getattr(module, function_name)
            patch_key = f"{module_name}.{function_name}"
            _original_implementations[patch_key] = original_function
            _rust_implementations[patch_key] = rust_function
            _patched_functions[patch_key] = feature_name

            # Create wrapper based on whether it's async
            import asyncio

            if asyncio.iscoroutinefunction(
                original_function
            ) or asyncio.iscoroutinefunction(rust_function):
                wrapper = AsyncPerformanceWrapper(
                    original_function, rust_function, feature_name
                )
            else:
                wrapper = PerformanceWrapper(
                    original_function, rust_function, feature_name
                )

            # Replace with wrapper
            setattr(module, function_name, wrapper)
            logger.info(
                f"Successfully patched {module_name}.{function_name} with feature flag {feature_name}"
            )
            return True
        else:
            logger.warning(f"Function {module_name}.{function_name} not found")
            return False

    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not patch {module_name}.{function_name}: {e}")
        return False


def enhanced_patch_class(
    module_name: str, class_name: str, rust_class: Any, feature_name: str
) -> bool:
    """
    Enhanced class patching with feature flags and monitoring.

    Args:
        module_name: Name of the module containing the class
        class_name: Name of the class to patch
        rust_class: Rust implementation to use
        feature_name: Feature flag name for this patch

    Returns:
        bool: True if patching was successful, False otherwise
    """
    try:
        # Import the module
        module = importlib.import_module(module_name)

        # Store the original class if it exists
        if hasattr(module, class_name):
            original_class = getattr(module, class_name)
            patch_key = f"{module_name}.{class_name}"
            _original_implementations[patch_key] = original_class
            _rust_implementations[patch_key] = rust_class
            _patched_functions[patch_key] = feature_name

            # Create a hybrid class that checks feature flags
            class HybridClass:
                def __new__(cls, *args, **kwargs):
                    request_id = kwargs.get("request_id")

                    if is_enabled(feature_name, request_id):
                        try:
                            start_time = time.perf_counter()
                            instance = rust_class(*args, **kwargs)
                            duration_ms = (time.perf_counter() - start_time) * 1000
                            record_performance(feature_name, duration_ms)
                            return instance
                        except Exception as e:
                            record_error(feature_name, e)
                            logger.warning(
                                f"Rust class instantiation failed for {feature_name}, falling back: {e}"
                            )

                    # Fallback to original class
                    return original_class(*args, **kwargs)

            # Copy attributes from original class (only safe, non-dunder attributes)
            # Exclude private/special attributes that could cause issues
            excluded_attrs = {
                "__class__", "__delattr__", "__dict__", "__doc__", "__format__",
                "__getattribute__", "__init__", "__init_subclass__", "__new__",
                "__reduce__", "__reduce_ex__", "__repr__", "__setattr__",
                "__subclasshook__", "__weakref__", "__mro_entries__", "__matches__",
            }
            for attr_name in dir(original_class):
                if not attr_name.startswith("_") or attr_name in ("__doc__", "__module__"):
                    if attr_name not in excluded_attrs:
                        try:
                            attr_value = getattr(original_class, attr_name)
                            # Only copy safe types
                            if not callable(attr_value) or attr_name in ("__doc__", "__module__"):
                                setattr(HybridClass, attr_name, attr_value)
                        except (AttributeError, TypeError):
                            pass

            # Replace with hybrid class
            setattr(module, class_name, HybridClass)
            logger.info(
                f"Successfully patched {module_name}.{class_name} with feature flag {feature_name}"
            )
            return True
        else:
            logger.warning(f"Class {module_name}.{class_name} not found")
            return False

    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not patch {module_name}.{class_name}: {e}")
        return False


def enhanced_apply_acceleration(rust_extensions_module) -> bool:
    """
    Apply Rust acceleration using enhanced patching with feature flags.

    Args:
        rust_extensions_module: The imported rust_extensions module

    Returns:
        bool: True if acceleration was applied successfully, False otherwise
    """
    if (
        not hasattr(rust_extensions_module, "RUST_ACCELERATION_AVAILABLE")
        or not rust_extensions_module.RUST_ACCELERATION_AVAILABLE
    ):
        logger.info(
            "Rust acceleration is not available. Falling back to Python implementations."
        )
        return False

    logger.info("Applying enhanced Rust acceleration with feature flags...")

    # Track successful patches
    success_count = 0
    total_patches = 0

    # Get the Rust extension modules
    try:
        fast_litellm = rust_extensions_module.fast_litellm
        _rust = rust_extensions_module._rust
    except AttributeError as e:
        logger.error(f"Could not access Rust extensions: {e}")
        return False

    # Patch routing components with feature flag
    if hasattr(fast_litellm, "AdvancedRouter"):
        total_patches += 1
        if enhanced_patch_class(
            "litellm.router", "Router", fast_litellm.AdvancedRouter, "rust_routing"
        ):
            success_count += 1

    # Patch token counting with feature flag
    if hasattr(_rust, "SimpleTokenCounter"):
        # Create a counter instance
        counter = _rust.SimpleTokenCounter(4096)

        # Create wrapper function that adapts LiteLLM's signature to our Rust function
        def rust_token_counter(model=None, messages=None, text=None, **kwargs):
            """Rust-accelerated token counter that matches LiteLLM's signature."""
            if text is not None:
                # Direct text provided
                return counter.count_tokens(text, model)

            if messages is not None:
                # Extract text from messages
                total_tokens = 0
                for msg in messages:
                    if isinstance(msg, dict):
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            total_tokens += counter.count_tokens(content, model)
                        elif isinstance(content, list):
                            # Handle content lists (for multimodal)
                            for part in content:
                                if (
                                    isinstance(part, dict)
                                    and part.get("type") == "text"
                                ):
                                    total_tokens += counter.count_tokens(
                                        part.get("text", ""), model
                                    )
                return total_tokens

            return 0

        # Patch both litellm.utils.token_counter AND litellm.token_counter
        total_patches += 1
        if enhanced_patch_function(
            "litellm.utils",
            "token_counter",
            rust_token_counter,
            "rust_token_counting",
        ):
            success_count += 1

        # Also patch the top-level litellm.token_counter
        total_patches += 1
        if enhanced_patch_function(
            "litellm",
            "token_counter",
            rust_token_counter,
            "rust_token_counting",
        ):
            success_count += 1

    # Patch rate limiting
    if hasattr(_rust, "SimpleRateLimiter"):
        total_patches += 1
        if enhanced_patch_class(
            "litellm",
            "SimpleRateLimiter",
            _rust.SimpleRateLimiter,
            "rust_rate_limiting",
        ):
            success_count += 1

    # Patch connection pooling
    if hasattr(_rust, "SimpleConnectionPool"):
        total_patches += 1
        if enhanced_patch_class(
            "litellm",
            "SimpleConnectionPool",
            _rust.SimpleConnectionPool,
            "rust_connection_pooling",
        ):
            success_count += 1

    # Add new batch processing function if available
    if hasattr(_rust, "SimpleTokenCounter"):
        counter = _rust.SimpleTokenCounter(100)
        if hasattr(counter, "count_tokens_batch"):
            total_patches += 1
            if enhanced_patch_function(
                "litellm.utils",
                "count_tokens_batch",
                counter.count_tokens_batch,
                "batch_token_counting",
            ):
                success_count += 1

    logger.info(
        f"Applied {success_count}/{total_patches} enhanced Rust acceleration patches successfully."
    )
    return success_count > 0


def remove_enhanced_acceleration() -> None:
    """
    Remove enhanced Rust acceleration and restore original Python implementations.
    """
    logger.info(
        "Removing enhanced Rust acceleration and restoring original implementations..."
    )

    for patch_key, original_impl in _original_implementations.items():
        try:
            module_name, attr_name = patch_key.rsplit(".", 1)
            module = importlib.import_module(module_name)
            setattr(module, attr_name, original_impl)
            logger.debug(f"Restored {patch_key}")
        except (ImportError, ValueError) as e:
            logger.warning(f"Could not restore {patch_key}: {e}")

    _original_implementations.clear()
    _rust_implementations.clear()
    _patched_functions.clear()
    logger.info("Restored original implementations.")


def get_patch_status() -> Dict[str, Any]:
    """Get the current status of all patches."""
    from .feature_flags import get_status

    feature_status = get_status()

    return {
        "patched_functions": {
            patch_key: {
                "feature_flag": feature_name,
                "enabled": is_enabled(feature_name),
                "has_original": patch_key in _original_implementations,
                "has_rust": patch_key in _rust_implementations,
            }
            for patch_key, feature_name in _patched_functions.items()
        },
        "feature_flags": feature_status,
        "total_patches": len(_patched_functions),
    }


@contextmanager
def temporary_disable_feature(feature_name: str):
    """
    Temporarily disable a feature for testing purposes.

    Args:
        feature_name: Name of the feature to disable
    """
    from .feature_flags import _feature_manager

    original_state = None
    try:
        with _feature_manager._lock:
            if feature_name in _feature_manager._features:
                original_state = _feature_manager._features[feature_name].state
                _feature_manager._features[feature_name].state = (
                    _feature_manager.FeatureState.DISABLED
                )

        yield

    finally:
        if original_state is not None:
            with _feature_manager._lock:
                if feature_name in _feature_manager._features:
                    _feature_manager._features[feature_name].state = original_state
