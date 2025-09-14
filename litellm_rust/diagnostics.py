"""
Health check and diagnostics for LiteLLM Rust acceleration.
"""
from typing import Dict, Any

from .rust_extensions import (
    RUST_ACCELERATION_AVAILABLE,
    litellm_core,
    litellm_token,
    litellm_connection_pool,
    litellm_rate_limiter,
)

def health_check() -> Dict[str, Any]:
    """
    Perform a comprehensive health check of all Rust components.
    
    Returns:
        Dict[str, Any]: Health check results
    """
    results = {
        "rust_acceleration_available": RUST_ACCELERATION_AVAILABLE,
        "components": {}
    }
    
    if not RUST_ACCELERATION_AVAILABLE:
        results["error"] = "Rust acceleration is not available"
        return results
    
    # Check core components
    core_results = {}
    if hasattr(litellm_core, "health_check"):
        try:
            core_results["core_healthy"] = litellm_core.health_check()
        except Exception as e:
            core_results["core_healthy"] = False
            core_results["error"] = str(e)
    
    if hasattr(litellm_core, "advanced_router_health_check"):
        try:
            core_results["router_healthy"] = litellm_core.advanced_router_health_check()
        except Exception as e:
            core_results["router_healthy"] = False
            core_results["router_error"] = str(e)
    
    results["components"]["core"] = core_results
    
    # Check token components
    token_results = {}
    if hasattr(litellm_token, "token_health_check"):
        try:
            token_results["token_healthy"] = litellm_token.token_health_check()
        except Exception as e:
            token_results["token_healthy"] = False
            token_results["error"] = str(e)
    
    results["components"]["token"] = token_results
    
    # Check connection pool components
    connection_pool_results = {}
    if hasattr(litellm_connection_pool, "connection_pool_health_check"):
        try:
            connection_pool_results["connection_pool_healthy"] = litellm_connection_pool.connection_pool_health_check()
        except Exception as e:
            connection_pool_results["connection_pool_healthy"] = False
            connection_pool_results["error"] = str(e)
    
    results["components"]["connection_pool"] = connection_pool_results
    
    # Check rate limiter components
    rate_limiter_results = {}
    if hasattr(litellm_rate_limiter, "rate_limit_health_check"):
        try:
            rate_limiter_results["rate_limiter_healthy"] = litellm_rate_limiter.rate_limit_health_check()
        except Exception as e:
            rate_limiter_results["rate_limiter_healthy"] = False
            rate_limiter_results["error"] = str(e)
    
    results["components"]["rate_limiter"] = rate_limiter_results
    
    # Overall health
    all_healthy = all(
        component.get("healthy", False) or 
        component.get("core_healthy", False) or
        component.get("token_healthy", False) or
        component.get("connection_pool_healthy", False) or
        component.get("rate_limiter_healthy", False)
        for component in results["components"].values()
    )
    
    results["overall_healthy"] = all_healthy
    
    return results

def get_performance_stats() -> Dict[str, Any]:
    """
    Get performance statistics from all Rust components.
    
    Returns:
        Dict[str, Any]: Performance statistics
    """
    stats = {
        "rust_acceleration_available": RUST_ACCELERATION_AVAILABLE,
        "components": {}
    }
    
    if not RUST_ACCELERATION_AVAILABLE:
        stats["error"] = "Rust acceleration is not available"
        return stats
    
    # Get core stats
    core_stats = {}
    if hasattr(litellm_core, "LiteLLMCore"):
        try:
            core = litellm_core.LiteLLMCore()
            if hasattr(core, "get_stats"):
                core_stats["stats"] = core.get_stats()
        except Exception as e:
            core_stats["error"] = str(e)
    
    stats["components"]["core"] = core_stats
    
    # Get token stats
    token_stats = {}
    if hasattr(litellm_token, "SimpleTokenCounter"):
        try:
            token_counter = litellm_token.SimpleTokenCounter(100)
            if hasattr(token_counter, "get_cache_stats"):
                token_stats["cache_stats"] = token_counter.get_cache_stats()
        except Exception as e:
            token_stats["error"] = str(e)
    
    stats["components"]["token"] = token_stats
    
    # Get rate limiter stats
    rate_limiter_stats = {}
    if hasattr(litellm_rate_limiter, "SimpleRateLimiter"):
        try:
            rate_limiter = litellm_rate_limiter.SimpleRateLimiter()
            if hasattr(rate_limiter, "get_rate_limit_stats"):
                rate_limiter_stats["stats"] = rate_limiter.get_rate_limit_stats()
        except Exception as e:
            rate_limiter_stats["error"] = str(e)
    
    stats["components"]["rate_limiter"] = rate_limiter_stats
    
    return stats