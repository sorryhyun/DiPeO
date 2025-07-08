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
        return not any(
            record.name.startswith(logger) for logger in self.excluded_loggers
        )


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
        force=True,  # Force reconfiguration
    )

    # Add filter to exclude noisy loggers
    # In debug mode, allow openai logs to see LLM interactions
    excluded_loggers = [
        "gql.transport",
        "websockets",
        "asyncio",
        "httpcore",
        "httpx",
        "hypercorn.access",
        "multipart",
        "python_multipart",
        "urllib3",
        "requests",
        "aiohttp",
    ]

    # Only exclude openai logs when not in debug mode
    if not debug:
        excluded_loggers.append("openai")

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

        # Enable debug logging for OpenAI to see API requests
        openai_logger = logging.getLogger("openai")
        openai_logger.setLevel(logging.DEBUG)
        httpx_logger = logging.getLogger("httpx")
        httpx_logger.setLevel(
            logging.INFO
        )  # INFO level to see requests without too much noise

        # Show which loggers are at DEBUG level
        debug_loggers = []
        for name in [
            "dipeo",
            "dipeo.core",
            "dipeo.domain",
            "dipeo.diagram",
            "dipeo.application",
            "dipeo.infra",
            "dipeo.container",
            "openai",
        ]:
            if logging.getLogger(name).getEffectiveLevel() <= logging.DEBUG:
                debug_loggers.append(name)
        if debug_loggers:
            logger.debug(f"DEBUG enabled for loggers: {', '.join(debug_loggers)}")
