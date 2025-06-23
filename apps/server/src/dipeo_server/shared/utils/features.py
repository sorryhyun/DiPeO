"""Feature flag management utilities."""

import os
from enum import Enum
from typing import Any, Dict, Optional


class FeatureFlag(Enum):
    """Feature flags for controlling application behavior."""

    # Core execution features
    ENABLE_STREAMING = "enable_streaming"
    ENABLE_COST_TRACKING = "enable_cost_tracking"
    ENABLE_MEMORY_PERSISTENCE = "enable_memory_persistence"

    # Performance features
    ENABLE_EXECUTOR_CACHING = "enable_executor_caching"
    ENABLE_PARALLEL_EXECUTION = "enable_parallel_execution"
    ENABLE_EXECUTION_MONITORING = "enable_execution_monitoring"

    # Safety features
    ENABLE_SANDBOX_MODE = "enable_sandbox_mode"
    ENABLE_EXECUTION_TIMEOUT = "enable_execution_timeout"
    ENABLE_RATE_LIMITING = "enable_rate_limiting"

    # Debug features
    ENABLE_DEBUG_MODE = "enable_debug_mode"
    ENABLE_VERBOSE_LOGGING = "enable_verbose_logging"
    ENABLE_EXECUTION_TRACING = "enable_execution_tracing"


class FeatureFlagManager:
    """Manages feature flags for the application."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize feature flag manager."""
        self._flags = config or {}
        self._load_from_environment()
        self._set_defaults()

    def _load_from_environment(self):
        """Load feature flags from environment variables."""
        for flag in FeatureFlag:
            env_var = f"DIPEO_{flag.value.upper()}"
            env_value = os.getenv(env_var)

            if env_value is not None:
                # Convert string to boolean
                self._flags[flag.value] = env_value.lower() in (
                    "true",
                    "1",
                    "yes",
                    "on",
                )

    def _set_defaults(self):
        """Set default values for feature flags."""
        defaults = {
            # Core execution features
            FeatureFlag.ENABLE_STREAMING.value: True,
            FeatureFlag.ENABLE_COST_TRACKING.value: True,
            FeatureFlag.ENABLE_MEMORY_PERSISTENCE.value: True,
            # Performance features
            FeatureFlag.ENABLE_EXECUTOR_CACHING.value: True,
            FeatureFlag.ENABLE_PARALLEL_EXECUTION.value: False,  # Not implemented yet
            FeatureFlag.ENABLE_EXECUTION_MONITORING.value: True,
            # Safety features
            FeatureFlag.ENABLE_SANDBOX_MODE.value: True,
            FeatureFlag.ENABLE_EXECUTION_TIMEOUT.value: True,
            FeatureFlag.ENABLE_RATE_LIMITING.value: False,  # Disabled for development
            # Debug features (disabled by default)
            FeatureFlag.ENABLE_DEBUG_MODE.value: False,
            FeatureFlag.ENABLE_VERBOSE_LOGGING.value: False,
            FeatureFlag.ENABLE_EXECUTION_TRACING.value: False,
        }

        for flag, default_value in defaults.items():
            if flag not in self._flags:
                self._flags[flag] = default_value

    def is_enabled(self, flag: FeatureFlag) -> bool:
        """Check if a feature flag is enabled."""
        return self._flags.get(flag.value, False)

    def enable(self, flag: FeatureFlag) -> None:
        """Enable a feature flag."""
        self._flags[flag.value] = True

    def disable(self, flag: FeatureFlag) -> None:
        """Disable a feature flag."""
        self._flags[flag.value] = False

    def set_flag(self, flag: FeatureFlag, value: bool) -> None:
        """Set a feature flag to a specific value."""
        self._flags[flag.value] = value

    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags and their current values."""
        return self._flags.copy()

    def reset_to_defaults(self) -> None:
        """Reset all flags to their default values."""
        self._flags.clear()
        self._set_defaults()


# Global feature flag manager instance
_feature_flags = FeatureFlagManager()


def is_feature_enabled(flag: FeatureFlag) -> bool:
    """Global function to check if a feature is enabled."""
    return _feature_flags.is_enabled(flag)


def enable_feature(flag: FeatureFlag) -> None:
    """Global function to enable a feature."""
    _feature_flags.enable(flag)


def disable_feature(flag: FeatureFlag) -> None:
    """Global function to disable a feature."""
    _feature_flags.disable(flag)


def configure_features(config: Dict[str, bool]) -> None:
    """Configure multiple features at once."""
    for flag_name, value in config.items():
        try:
            flag = FeatureFlag(flag_name)
            _feature_flags.set_flag(flag, value)
        except ValueError:
            # Unknown flag, ignore
            pass


def get_feature_flags() -> Dict[str, bool]:
    """Get all current feature flags."""
    return _feature_flags.get_all_flags()


# Feature status reporting
def get_feature_status() -> Dict[str, Any]:
    """Get current feature status."""
    return {
        "streaming_enabled": is_feature_enabled(FeatureFlag.ENABLE_STREAMING),
        "cost_tracking_enabled": is_feature_enabled(FeatureFlag.ENABLE_COST_TRACKING),
        "memory_persistence_enabled": is_feature_enabled(
            FeatureFlag.ENABLE_MEMORY_PERSISTENCE
        ),
        "executor_caching_enabled": is_feature_enabled(
            FeatureFlag.ENABLE_EXECUTOR_CACHING
        ),
        "monitoring_enabled": is_feature_enabled(
            FeatureFlag.ENABLE_EXECUTION_MONITORING
        ),
        "sandbox_mode_enabled": is_feature_enabled(FeatureFlag.ENABLE_SANDBOX_MODE),
    }
