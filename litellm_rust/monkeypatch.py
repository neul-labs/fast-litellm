"""
LiteLLM Rust Acceleration - Monkeypatching Implementation

This module provides the actual monkeypatching logic to replace LiteLLM classes
with their Rust-accelerated counterparts.
"""

import importlib
import sys
from typing import Any, Dict, Optional, Union
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Store references to original classes for potential fallback
_original_classes: Dict[str, Any] = {}

def _get_class_from_module(module_name: str, class_name: str) -> Optional[Any]:
    """
    Safely get a class from a module.
    
    Args:
        module_name: Name of the module
        class_name: Name of the class to get
        
    Returns:
        The class if found, None otherwise
    """
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, class_name):
            return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.debug(f"Could not get {module_name}.{class_name}: {e}")
        return None
    return None

def _patch_class(module_name: str, class_name: str, rust_class: Any) -> bool:
    """
    Patch a class in a module with a Rust implementation.
    
    Args:
        module_name: Name of the module containing the class
        class_name: Name of the class to patch
        rust_class: Rust implementation to use
        
    Returns:
        bool: True if patching was successful, False otherwise
    """
    try:
        # Import the module
        module = importlib.import_module(module_name)
        
        # Store the original class if it exists
        if hasattr(module, class_name):
            original_class = getattr(module, class_name)
            _original_classes[f"{module_name}.{class_name}"] = original_class
            logger.debug(f"Stored original {module_name}.{class_name}")
        
        # Replace with Rust implementation
        setattr(module, class_name, rust_class)
        logger.info(f"Successfully patched {module_name}.{class_name} with Rust implementation")
        return True
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not patch {module_name}.{class_name}: {e}")
        return False

def _patch_function(module_name: str, function_name: str, rust_function: Any) -> bool:
    """
    Patch a function in a module with a Rust implementation.
    
    Args:
        module_name: Name of the module containing the function
        function_name: Name of the function to patch
        rust_function: Rust implementation to use
        
    Returns:
        bool: True if patching was successful, False otherwise
    """
    try:
        # Import the module
        module = importlib.import_module(module_name)
        
        # Store the original function if it exists
        if hasattr(module, function_name):
            original_function = getattr(module, function_name)
            _original_classes[f"{module_name}.{function_name}"] = original_function
            logger.debug(f"Stored original {module_name}.{function_name}")
        
        # Replace with Rust implementation
        setattr(module, function_name, rust_function)
        logger.info(f"Successfully patched {module_name}.{function_name} with Rust implementation")
        return True
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not patch {module_name}.{function_name}: {e}")
        return False

def apply_acceleration(rust_extensions_module) -> bool:
    """
    Apply Rust acceleration by monkeypatching LiteLLM classes.
    
    Args:
        rust_extensions_module: The imported rust_extensions module
        
    Returns:
        bool: True if acceleration was applied successfully, False otherwise
    """
    if not hasattr(rust_extensions_module, 'RUST_ACCELERATION_AVAILABLE') or \
       not rust_extensions_module.RUST_ACCELERATION_AVAILABLE:
        logger.info("Rust acceleration is not available. Falling back to Python implementations.")
        return False
    
    logger.info("Applying Rust acceleration to LiteLLM components...")
    
    # Track successful patches
    success_count = 0
    total_patches = 0
    
    # Get the Rust extension modules
    try:
        litellm_core = rust_extensions_module.litellm_core
        litellm_token = rust_extensions_module.litellm_token
        litellm_connection_pool = rust_extensions_module.litellm_connection_pool
        litellm_rate_limiter = rust_extensions_module.litellm_rate_limiter
    except AttributeError as e:
        logger.error(f"Could not access Rust extensions: {e}")
        return False
    
    # Patch main Router class - replace with our AdvancedRouter
    # Note: This requires API compatibility verification
    if hasattr(litellm_core, "AdvancedRouter"):
        total_patches += 1
        if _patch_class("litellm.router", "Router", litellm_core.AdvancedRouter):
            success_count += 1
    
    # Patch Deployment class in types.router
    if hasattr(litellm_core, "Deployment"):
        total_patches += 1
        if _patch_class("litellm.types.router", "Deployment", litellm_core.Deployment):
            success_count += 1
    
    # Patch RoutingStrategy enum
    if hasattr(litellm_core, "RoutingStrategy"):
        total_patches += 1
        if _patch_class("litellm.types.router", "RoutingStrategy", litellm_core.RoutingStrategy):
            success_count += 1
    
    # Provide new utility classes (these don't exist in original LiteLLM)
    if hasattr(litellm_token, "SimpleTokenCounter"):
        total_patches += 1
        if _patch_class("litellm", "SimpleTokenCounter", litellm_token.SimpleTokenCounter):
            success_count += 1
    
    if hasattr(litellm_rate_limiter, "SimpleRateLimiter"):
        total_patches += 1
        if _patch_class("litellm", "SimpleRateLimiter", litellm_rate_limiter.SimpleRateLimiter):
            success_count += 1
    
    if hasattr(litellm_connection_pool, "SimpleConnectionPool"):
        total_patches += 1
        if _patch_class("litellm", "SimpleConnectionPool", litellm_connection_pool.SimpleConnectionPool):
            success_count += 1
    
    # Patch health check functions
    if hasattr(litellm_core, "health_check"):
        total_patches += 1
        if _patch_function("litellm", "health_check", litellm_core.health_check):
            success_count += 1
    
    if hasattr(litellm_core, "advanced_router_health_check"):
        total_patches += 1
        if _patch_function("litellm.router", "advanced_router_health_check", litellm_core.advanced_router_health_check):
            success_count += 1
    
    if hasattr(litellm_token, "token_health_check"):
        total_patches += 1
        if _patch_function("litellm", "token_health_check", litellm_token.token_health_check):
            success_count += 1
    
    if hasattr(litellm_connection_pool, "connection_pool_health_check"):
        total_patches += 1
        if _patch_function("litellm", "connection_pool_health_check", litellm_connection_pool.connection_pool_health_check):
            success_count += 1
    
    if hasattr(litellm_rate_limiter, "rate_limit_health_check"):
        total_patches += 1
        if _patch_function("litellm", "rate_limit_health_check", litellm_rate_limiter.rate_limit_health_check):
            success_count += 1
    
    logger.info(f"Applied {success_count}/{total_patches} Rust acceleration patches successfully.")
    return success_count > 0

def remove_acceleration() -> None:
    """
    Remove Rust acceleration and restore original Python implementations.
    """
    logger.info("Removing Rust acceleration and restoring original implementations...")
    
    for qualified_name, original_class in _original_classes.items():
        try:
            module_name, class_name = qualified_name.rsplit(".", 1)
            module = importlib.import_module(module_name)
            setattr(module, class_name, original_class)
            logger.debug(f"Restored {qualified_name}")
        except (ImportError, ValueError) as e:
            logger.warning(f"Could not restore {qualified_name}: {e}")
    
    _original_classes.clear()
    logger.info("Restored original implementations.")

# Automatically apply acceleration when the module is imported
def auto_apply_acceleration():
    """
    Automatically apply acceleration when this module is imported.
    """
    try:
        # Import the rust extensions
        from . import rust_extensions
        if rust_extensions.RUST_ACCELERATION_AVAILABLE:
            apply_acceleration(rust_extensions)
        else:
            logger.info("Rust acceleration is not available. Install with Rust components for better performance.")
    except ImportError as e:
        logger.warning(f"Could not import rust_extensions: {e}")

# Apply acceleration automatically
auto_apply_acceleration()