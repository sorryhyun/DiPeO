"""Logging configuration for DiPeO CLI"""

import logging
import os


class ExcludeFilter(logging.Filter):
    """Filter to exclude specific loggers from output"""
    
    def __init__(self, excluded_loggers):
        super().__init__()
        self.excluded_loggers = excluded_loggers
    
    def filter(self, record):
        # Return False to exclude, True to include
        return not any(record.name.startswith(logger) for logger in self.excluded_loggers)


def configure_logging(debug: bool = False) -> None:
    """Configure logging for the CLI.
    
    Args:
        debug: Whether to enable debug logging
    """
    # Determine log level
    log_level = "DEBUG" if debug else os.environ.get("LOG_LEVEL", "INFO")
    
    # Configure basic logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True  # Force reconfiguration
    )
    
    # Add filter to exclude noisy loggers
    excluded_loggers = [
        "gql.transport",
        "websockets",
        "asyncio",
        "httpcore",
        "httpx",
        "openai",
        "hypercorn.access",
        "multipart",
        "python_multipart",
        "urllib3",
        "requests",
        "aiohttp"
    ]
    
    # Get root logger and add filter
    root_logger = logging.getLogger()
    exclude_filter = ExcludeFilter(excluded_loggers)
    
    # Add filter to all handlers
    for handler in root_logger.handlers:
        handler.addFilter(exclude_filter)
    
    # Create logger for CLI itself
    logger = logging.getLogger("dipeo_cli")
    
    if debug:
        logger.debug("Debug logging enabled for DiPeO CLI")
        # Show which loggers are at DEBUG level
        debug_loggers = []
        for name in ["dipeo", "dipeo_core", "dipeo_domain", "dipeo_diagram", 
                     "dipeo_application", "dipeo_infra", "dipeo_container"]:
            if logging.getLogger(name).getEffectiveLevel() <= logging.DEBUG:
                debug_loggers.append(name)
        if debug_loggers:
            logger.debug(f"DEBUG enabled for loggers: {', '.join(debug_loggers)}")