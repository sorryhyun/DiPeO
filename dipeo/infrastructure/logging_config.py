"""Centralized logging configuration for DiPeO."""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging(
    component: str = "dipeo",
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_dir: str = ".logs",
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure logging for DiPeO components.

    Args:
        component: Component name (e.g., 'server', 'cli', 'worker')
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to write logs to file
        log_dir: Directory for log files (relative to DIPEO_BASE_DIR)
        console_output: Whether to output to console

    Returns:
        Configured logger instance
    """
    # Get base directory from environment
    base_dir = os.environ.get("DIPEO_BASE_DIR", os.getcwd())
    log_path = Path(base_dir) / log_dir

    # Create logs directory if it doesn't exist
    if log_to_file:
        log_path.mkdir(exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)

    # File handlers
    if log_to_file:
        # Main log file - overwrite on each run
        log_file = log_path / f"{component}.log"
        file_handler = logging.FileHandler(
            log_file,
            mode="w",  # Overwrite mode
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

        # Error log file - overwrite on each run
        error_log_file = log_path / f"{component}.error.log"
        error_handler = logging.FileHandler(
            error_log_file,
            mode="w",  # Overwrite mode
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)

        # Daily log file for important events - append mode for daily accumulation
        daily_log_file = log_path / f"{component}.{datetime.now().strftime('%Y%m%d')}.log"
        daily_handler = logging.FileHandler(
            daily_log_file,
            mode="a",  # Append mode for daily logs
            encoding="utf-8",
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(simple_formatter)
        root_logger.addHandler(daily_handler)

    # Configure noisy loggers
    suppress_noisy_loggers(log_level)

    # Get component logger
    logger = logging.getLogger(component)

    # Log initialization
    if log_to_file:
        logger.info(f"Logging initialized for {component} - Files: {log_path}")
    else:
        logger.info(f"Logging initialized for {component} - Console only")

    return logger


def suppress_noisy_loggers(log_level: str = "INFO"):
    """Suppress noisy third-party loggers."""
    # Always suppress these noisy loggers
    noisy_loggers = [
        "asyncio",
        "httpcore",
        "httpx",
        "openai",
        "openai._base_client",
        "hypercorn.access",
        "multipart",
        "python_multipart",
        "urllib3",
        "requests",
        "strawberry",
        "watchfiles",
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Reduce verbose debug logging from execution components in non-DEBUG mode
    if log_level != "DEBUG":
        verbose_loggers = [
            "dipeo.infrastructure.events.observer_adapter",
            "dipeo.infrastructure.utils.single_flight_cache",
            "dipeo.infrastructure.llm.adapters.openai",
            "dipeo.application.execution.states.node_readiness_checker",
            "dipeo.application.execution.handlers.person_job.single_executor",
            "dipeo.application.execution.handlers.condition.evaluators",
        ]

        for logger_name in verbose_loggers:
            logging.getLogger(logger_name).setLevel(logging.INFO)


def get_execution_logger(execution_id: str) -> logging.Logger:
    """
    Get a logger for a specific execution.

    This creates a separate log file for each execution to make debugging easier.
    """
    base_dir = os.environ.get("DIPEO_BASE_DIR", os.getcwd())
    log_path = Path(base_dir) / ".logs" / "executions"
    log_path.mkdir(parents=True, exist_ok=True)

    # Create execution-specific logger
    logger = logging.getLogger(f"execution.{execution_id}")

    # Don't propagate to root logger to avoid duplication
    logger.propagate = False

    # Create file handler for this execution
    log_file = log_path / f"{execution_id}.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)  # Capture all for executions

    return logger
