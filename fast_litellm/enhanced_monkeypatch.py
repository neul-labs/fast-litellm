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

from .feature_flags import is_enabled, record_error, record_performance

logger = logging.getLogger(__name__)

# Store references to original classes and functions
_original_implementations: Dict[str, Any] = {}
_rust_implementations: Dict[str, Any] = {}
_patched_functions: Dict[str, str] = {}  # Maps function -> feature flag name


class PerformanceWrapper:
    """Wrapper that measures performance and handles fallback."""

    def __init__(self, original_func: Callable, rust_func: Callable, feature_name: str):
        self.original_func = original_func
        self.rust_func = rust_func
        self.feature_name = feature_name
        functools.update_wrapper(self, original_func)

    def __call__(self, *args, **kwargs):
        """Execute with performance monitoring and fallback."""
        request_id = kwargs.get("request_id") or getattr(
            args[0] if args else None, "request_id", None
        )

        if not is_enabled(self.feature_name, request_id):
            # Feature disabled, use original implementation
            return self.original_func(*args, **kwargs)

        start_time = time.perf_counter()
        try:
            # Try Rust implementation
            result = self.rust_func(*args, **kwargs)

            # Record successful performance
            duration_ms = (time.perf_counter() - start_time) * 1000
            record_performance(self.feature_name, duration_ms)

            return result

        except Exception as e:
            # Record error and fallback to original
            record_error(self.feature_name, e)
            logger.warning(
                f"Rust implementation failed for {self.feature_name}, falling back to Python: {e}"
            )

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
    """Async version of PerformanceWrapper."""

    def __init__(self, original_func: Callable, rust_func: Callable, feature_name: str):
        self.original_func = original_func
        self.rust_func = rust_func
        self.feature_name = feature_name
        functools.update_wrapper(self, original_func)

    async def __call__(self, *args, **kwargs):
        """Execute async with performance monitoring and fallback."""
        request_id = kwargs.get("request_id") or getattr(
            args[0] if args else None, "request_id", None
        )

        if not is_enabled(self.feature_name, request_id):
            # Feature disabled, use original implementation
            if asyncio.iscoroutinefunction(self.original_func):
                return await self.original_func(*args, **kwargs)
            else:
                return self.original_func(*args, **kwargs)

        start_time = time.perf_counter()
        try:
            # Try Rust implementation
            if asyncio.iscoroutinefunction(self.rust_func):
                result = await self.rust_func(*args, **kwargs)
            else:
                result = self.rust_func(*args, **kwargs)

            # Record successful performance
            duration_ms = (time.perf_counter() - start_time) * 1000
            record_performance(self.feature_name, duration_ms)

            return result

        except Exception as e:
            # Record error and fallback to original
            record_error(self.feature_name, e)
            logger.warning(
                f"Rust implementation failed for {self.feature_name}, falling back to Python: {e}"
            )

            try:
                if asyncio.iscoroutinefunction(self.original_func):
                    return await self.original_func(*args, **kwargs)
                else:
                    return self.original_func(*args, **kwargs)
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

            # Copy attributes from original class
            for attr_name in dir(original_class):
                if not attr_name.startswith("__") or attr_name in (
                    "__doc__",
                    "__module__",
                ):
                    try:
                        setattr(
                            HybridClass, attr_name, getattr(original_class, attr_name)
                        )
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
        _rust = rust_extensions_module._rust
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
