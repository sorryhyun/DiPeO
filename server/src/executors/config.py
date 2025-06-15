"""
Configuration for executor system.
"""

import os
from typing import Optional


class ExecutorConfig:
    """Configuration settings for the executor system."""
    
    # Whether to use the unified executor system
    USE_UNIFIED_EXECUTOR: bool = os.getenv("USE_UNIFIED_EXECUTOR", "false").lower() == "true"
    
    # Logging configuration
    LOG_EXECUTOR_METRICS: bool = os.getenv("LOG_EXECUTOR_METRICS", "true").lower() == "true"
    LOG_EXECUTOR_DETAILS: bool = os.getenv("LOG_EXECUTOR_DETAILS", "false").lower() == "true"
    
    # Error handling configuration
    MAX_RETRIES: int = int(os.getenv("EXECUTOR_MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("EXECUTOR_RETRY_DELAY", "1.0"))
    ERROR_RATE_THRESHOLD: float = float(os.getenv("EXECUTOR_ERROR_RATE_THRESHOLD", "0.5"))
    
    @classmethod
    def is_unified_enabled(cls) -> bool:
        """Check if unified executor is enabled."""
        return cls.USE_UNIFIED_EXECUTOR
    
    @classmethod
    def enable_unified(cls) -> None:
        """Enable unified executor (for testing)."""
        cls.USE_UNIFIED_EXECUTOR = True
    
    @classmethod
    def disable_unified(cls) -> None:
        """Disable unified executor (for testing)."""
        cls.USE_UNIFIED_EXECUTOR = False


# Global instance
executor_config = ExecutorConfig()