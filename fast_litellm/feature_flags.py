"""
Feature flag system for LiteLLM Rust acceleration.

This module provides a flexible feature flag system that allows for gradual
rollout of Rust acceleration features with automatic degradation capabilities.
"""

import json
import logging
import os
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)


class FeatureState(Enum):
    """States for feature flags."""

    DISABLED = "disabled"
    ENABLED = "enabled"
    CANARY = "canary"  # Enable for small percentage of traffic
    SHADOW = "shadow"  # Run in shadow mode (collect metrics, don't change behavior)
    GRADUAL_ROLLOUT = "gradual_rollout"  # Gradual percentage-based rollout


@dataclass
class FeatureConfig:
    """Configuration for a feature flag."""

    name: str
    state: FeatureState
    rollout_percentage: float = 0.0  # 0-100
    fallback_on_error: bool = True
    error_threshold: int = 5  # Number of errors before auto-disable
    performance_threshold_ms: float = 1000.0  # Auto-disable if slower than this
    dependencies: Set[str] = None  # Required features to be enabled

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = set()


class FeatureFlagManager:
    """
    Manages feature flags for LiteLLM Rust acceleration.

    Features:
    - Environment variable configuration
    - Automatic degradation on errors
    - Performance-based rollback
    - Gradual rollout support
    - Dependency management
    """

    def __init__(self):
        self._features: Dict[str, FeatureConfig] = {}
        self._error_counts: Dict[str, int] = {}
        self._performance_metrics: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._load_config()

    def _load_config(self):
        """Load feature flag configuration from environment variables and files."""

        # Default feature flags
        default_features = {
            "rust_routing": FeatureConfig(
                name="rust_routing",
                state=FeatureState.ENABLED,
                rollout_percentage=100.0,
                fallback_on_error=True,
                error_threshold=10,
                performance_threshold_ms=500.0,
            ),
            "rust_token_counting": FeatureConfig(
                name="rust_token_counting",
                state=FeatureState.ENABLED,
                rollout_percentage=100.0,
                fallback_on_error=True,
                error_threshold=5,
                performance_threshold_ms=100.0,
            ),
            "rust_rate_limiting": FeatureConfig(
                name="rust_rate_limiting",
                state=FeatureState.ENABLED,
                rollout_percentage=90.0,
                fallback_on_error=True,
                error_threshold=3,
            ),
            "rust_connection_pooling": FeatureConfig(
                name="rust_connection_pooling",
                state=FeatureState.GRADUAL_ROLLOUT,
                rollout_percentage=50.0,
                fallback_on_error=True,
                error_threshold=5,
            ),
            "batch_token_counting": FeatureConfig(
                name="batch_token_counting",
                state=FeatureState.CANARY,
                rollout_percentage=10.0,
                fallback_on_error=True,
                dependencies={"rust_token_counting"},
            ),
            "async_routing": FeatureConfig(
                name="async_routing",
                state=FeatureState.SHADOW,
                rollout_percentage=5.0,
                fallback_on_error=True,
                dependencies={"rust_routing"},
            ),
            "performance_monitoring": FeatureConfig(
                name="performance_monitoring",
                state=FeatureState.ENABLED,
                rollout_percentage=100.0,
                fallback_on_error=False,
            ),
        }

        with self._lock:
            self._features.update(default_features)

        # Override with environment variables
        self._load_env_overrides()

        # Load from config file if available
        config_file = os.environ.get("LITELLM_RUST_FEATURE_CONFIG")
        if config_file and os.path.exists(config_file):
            self._load_config_file(config_file)

    def _load_env_overrides(self):
        """Load feature flag overrides from environment variables."""

        # Global enable/disable
        if os.environ.get("LITELLM_RUST_DISABLE_ALL") == "true":
            with self._lock:
                for feature in self._features.values():
                    feature.state = FeatureState.DISABLED
            return

        # Individual feature overrides
        for feature_name in self._features:
            env_key = f"LITELLM_RUST_{feature_name.upper()}"
            env_value = os.environ.get(env_key)

            if env_value:
                try:
                    if env_value.lower() in ("true", "enabled"):
                        state = FeatureState.ENABLED
                        percentage = 100.0
                    elif env_value.lower() in ("false", "disabled"):
                        state = FeatureState.DISABLED
                        percentage = 0.0
                    elif env_value.startswith("canary:"):
                        state = FeatureState.CANARY
                        percentage = float(env_value.split(":")[1])
                    elif env_value.startswith("rollout:"):
                        state = FeatureState.GRADUAL_ROLLOUT
                        percentage = float(env_value.split(":")[1])
                    else:
                        continue

                    with self._lock:
                        if feature_name in self._features:
                            self._features[feature_name].state = state
                            self._features[feature_name].rollout_percentage = percentage

                except (ValueError, IndexError):
                    logger.warning(
                        f"Invalid feature flag value for {env_key}: {env_value}"
                    )

    def _load_config_file(self, config_file: str):
        """Load feature flags from a JSON configuration file."""
        try:
            with open(config_file, "r") as f:
                config = json.load(f)

            for feature_name, feature_config in config.get("features", {}).items():
                if feature_name in self._features:
                    with self._lock:
                        feature = self._features[feature_name]
                        feature.state = FeatureState(
                            feature_config.get("state", feature.state.value)
                        )
                        feature.rollout_percentage = feature_config.get(
                            "rollout_percentage", feature.rollout_percentage
                        )
                        feature.error_threshold = feature_config.get(
                            "error_threshold", feature.error_threshold
                        )
                        feature.performance_threshold_ms = feature_config.get(
                            "performance_threshold_ms", feature.performance_threshold_ms
                        )

        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to load feature config from {config_file}: {e}")

    def is_enabled(self, feature_name: str, request_id: Optional[str] = None) -> bool:
        """
        Check if a feature is enabled for the current request.

        Args:
            feature_name: Name of the feature to check
            request_id: Optional request ID for consistent rollout decisions

        Returns:
            True if the feature should be enabled, False otherwise
        """
        with self._lock:
            if feature_name not in self._features:
                return False

            feature = self._features[feature_name]

            # Check dependencies first
            for dep in feature.dependencies:
                if not self.is_enabled(dep, request_id):
                    return False

            # Check state
            if feature.state == FeatureState.DISABLED:
                return False
            elif feature.state == FeatureState.ENABLED:
                return True
            elif feature.state in (
                FeatureState.CANARY,
                FeatureState.GRADUAL_ROLLOUT,
                FeatureState.SHADOW,
            ):
                # Use consistent rollout based on request_id or random
                if request_id:
                    import hashlib

                    hash_value = int(
                        hashlib.md5(
                            f"{feature_name}:{request_id}".encode()
                        ).hexdigest()[:8],
                        16,
                    )
                    percentage = (hash_value % 100) + 1
                else:
                    import random

                    percentage = random.randint(1, 100)

                return percentage <= feature.rollout_percentage

        return False

    def record_error(self, feature_name: str, error: Exception):
        """
        Record an error for a feature and potentially disable it.

        Args:
            feature_name: Name of the feature that encountered an error
            error: The exception that occurred
        """
        with self._lock:
            if feature_name not in self._features:
                return

            feature = self._features[feature_name]
            if not feature.fallback_on_error:
                return

            self._error_counts[feature_name] = (
                self._error_counts.get(feature_name, 0) + 1
            )

            if self._error_counts[feature_name] >= feature.error_threshold:
                logger.warning(
                    f"Disabling feature '{feature_name}' due to {self._error_counts[feature_name]} errors. "
                    f"Latest error: {error}"
                )
                feature.state = FeatureState.DISABLED
                self._error_counts[feature_name] = 0  # Reset counter

    def record_performance(self, feature_name: str, duration_ms: float):
        """
        Record performance metrics for a feature.

        Args:
            feature_name: Name of the feature
            duration_ms: Duration in milliseconds
        """
        with self._lock:
            if feature_name not in self._features:
                return

            feature = self._features[feature_name]

            # Update rolling average
            if feature_name in self._performance_metrics:
                # Simple exponential moving average
                self._performance_metrics[feature_name] = (
                    0.9 * self._performance_metrics[feature_name] + 0.1 * duration_ms
                )
            else:
                self._performance_metrics[feature_name] = duration_ms

            # Check if performance is too slow
            if (
                duration_ms > feature.performance_threshold_ms
                and feature.fallback_on_error
                and feature.state != FeatureState.DISABLED
            ):

                logger.warning(
                    f"Disabling feature '{feature_name}' due to poor performance: "
                    f"{duration_ms:.2f}ms > {feature.performance_threshold_ms}ms threshold"
                )
                feature.state = FeatureState.DISABLED

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of all feature flags."""
        with self._lock:
            return {
                "features": {
                    name: {
                        "state": feature.state.value,
                        "rollout_percentage": feature.rollout_percentage,
                        "error_count": self._error_counts.get(name, 0),
                        "avg_performance_ms": self._performance_metrics.get(name, 0.0),
                        "dependencies": list(feature.dependencies),
                    }
                    for name, feature in self._features.items()
                },
                "global_status": {
                    "total_features": len(self._features),
                    "enabled_features": sum(
                        1
                        for f in self._features.values()
                        if f.state != FeatureState.DISABLED
                    ),
                    "error_count": sum(self._error_counts.values()),
                },
            }

    def reset_errors(self, feature_name: Optional[str] = None):
        """Reset error counts for a specific feature or all features."""
        with self._lock:
            if feature_name:
                self._error_counts.pop(feature_name, None)
            else:
                self._error_counts.clear()


# Global instance
_feature_manager = FeatureFlagManager()


def is_enabled(feature_name: str, request_id: Optional[str] = None) -> bool:
    """Check if a feature is enabled."""
    return _feature_manager.is_enabled(feature_name, request_id)


def record_error(feature_name: str, error: Exception):
    """Record an error for a feature."""
    _feature_manager.record_error(feature_name, error)


def record_performance(feature_name: str, duration_ms: float):
    """Record performance metrics for a feature."""
    _feature_manager.record_performance(feature_name, duration_ms)


def get_status() -> Dict[str, Any]:
    """Get the current status of all feature flags."""
    return _feature_manager.get_status()


def reset_errors(feature_name: Optional[str] = None):
    """Reset error counts."""
    _feature_manager.reset_errors(feature_name)
