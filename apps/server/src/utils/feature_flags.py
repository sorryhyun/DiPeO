"""Feature flags for controlling migration and rollout."""

import os
from typing import Dict, Any, Optional
from enum import Enum


class FeatureFlag(Enum):
    """Available feature flags."""
    
    # Execution Engine Flags
    USE_V2_EXECUTION = "use_v2_execution"
    ENABLE_STREAMING = "enable_streaming"
    ENABLE_COST_TRACKING = "enable_cost_tracking"
    ENABLE_MEMORY_PERSISTENCE = "enable_memory_persistence"
    
    # Performance Flags
    ENABLE_EXECUTOR_CACHING = "enable_executor_caching"
    ENABLE_PARALLEL_EXECUTION = "enable_parallel_execution"
    ENABLE_EXECUTION_MONITORING = "enable_execution_monitoring"
    
    # Safety Flags
    ENABLE_SANDBOX_MODE = "enable_sandbox_mode"
    ENABLE_EXECUTION_TIMEOUT = "enable_execution_timeout"
    ENABLE_RATE_LIMITING = "enable_rate_limiting"
    
    # Debug Flags
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
                self._flags[flag.value] = env_value.lower() in ('true', '1', 'yes', 'on')
    
    def _set_defaults(self):
        """Set default values for feature flags."""
        defaults = {
            # V2 execution is enabled by default (migration complete)
            FeatureFlag.USE_V2_EXECUTION.value: True,
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


class MigrationStrategy:
    """Handles migration strategy and rollback plans."""
    
    def __init__(self, feature_flags: FeatureFlagManager):
        self.feature_flags = feature_flags
    
    def enable_v2_execution(self) -> None:
        """Enable V2 execution engine."""
        self.feature_flags.enable(FeatureFlag.USE_V2_EXECUTION)
        self.feature_flags.enable(FeatureFlag.ENABLE_STREAMING)
        self.feature_flags.enable(FeatureFlag.ENABLE_COST_TRACKING)
    
    def rollback_to_v1(self) -> None:
        """Rollback to V1 execution (emergency rollback)."""
        self.feature_flags.disable(FeatureFlag.USE_V2_EXECUTION)
        # Keep other features that work with V1
    
    def enable_gradual_rollout(self, percentage: float = 50.0) -> None:
        """Enable gradual rollout of V2 features."""
        import random
        
        # Simple percentage-based rollout
        if random.random() * 100 < percentage:
            self.enable_v2_execution()
        else:
            self.rollback_to_v1()
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        return {
            "v2_execution_enabled": self.feature_flags.is_enabled(FeatureFlag.USE_V2_EXECUTION),
            "streaming_enabled": self.feature_flags.is_enabled(FeatureFlag.ENABLE_STREAMING),
            "cost_tracking_enabled": self.feature_flags.is_enabled(FeatureFlag.ENABLE_COST_TRACKING),
            "memory_persistence_enabled": self.feature_flags.is_enabled(FeatureFlag.ENABLE_MEMORY_PERSISTENCE),
            "migration_phase": "complete" if self.feature_flags.is_enabled(FeatureFlag.USE_V2_EXECUTION) else "v1_fallback"
        }


# Global migration strategy instance
migration_strategy = MigrationStrategy(_feature_flags)


def get_migration_status() -> Dict[str, Any]:
    """Get current migration status."""
    return migration_strategy.get_migration_status()


def emergency_rollback() -> None:
    """Emergency rollback to V1 execution."""
    migration_strategy.rollback_to_v1()


def enable_v2_migration() -> None:
    """Enable V2 migration."""
    migration_strategy.enable_v2_execution()