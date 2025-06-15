"""
Configuration for executor system.
"""

import os
from typing import Optional


class ExecutorConfig:
    """Configuration settings for the executor system."""
    
    # Logging configuration
    LOG_EXECUTOR_METRICS: bool = os.getenv("LOG_EXECUTOR_METRICS", "true").lower() == "true"
    LOG_EXECUTOR_DETAILS: bool = os.getenv("LOG_EXECUTOR_DETAILS", "false").lower() == "true"
    
    # Error handling configuration
    MAX_RETRIES: int = int(os.getenv("EXECUTOR_MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("EXECUTOR_RETRY_DELAY", "1.0"))
    ERROR_RATE_THRESHOLD: float = float(os.getenv("EXECUTOR_ERROR_RATE_THRESHOLD", "0.5"))


# Global instance
executor_config = ExecutorConfig()