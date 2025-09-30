"""Centralized base logger configuration for DiPeO.

This module provides a consistent logger pattern that all DiPeO modules should use.
It integrates with the existing LoggingMixin and provides a clean interface for logging.

Migration Notes:
- All modules should use `logger = logging.getLogger(__name__)` (not `log`)
- Classes can inherit from DiPeOLogger or LoggingMixin for consistent logging
- The standard variable name is `logger` for consistency across the codebase
"""

import logging
from typing import Optional


class DiPeOLogger:
    """Base logger class that provides consistent logging patterns for DiPeO.

    Usage:
        class MyService(DiPeOLogger):
            def __init__(self):
                super().__init__()
                self.logger.info("Service initialized")

    Or for standalone usage:
        logger = DiPeOLogger.get_logger(__name__)
        logger.info("Message")
    """

    def __init__(self):
        """Initialize the logger for the current class."""
        self._logger: Optional[logging.Logger] = None

    @property
    def logger(self) -> logging.Logger:
        """Get or create logger for this instance.

        This property ensures consistent naming patterns:
        - For classes: module.ClassName
        - For modules: use __name__ directly
        """
        if self._logger is None:
            if hasattr(self, '__class__'):
                # For class instances, use module.ClassName pattern
                logger_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
            else:
                # Fallback to module name
                logger_name = __name__

            self._logger = logging.getLogger(logger_name)

        return self._logger

    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """Get a logger with the specified name.

        Args:
            name: Logger name. If None, uses the calling module's __name__.
                  Typically pass __name__ from the calling module.

        Returns:
            Configured logger instance

        Example:
            logger = DiPeOLogger.get_logger(__name__)
        """
        if name is None:
            # Try to get the caller's module name
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back:
                name = frame.f_back.f_globals.get('__name__', 'dipeo')
            else:
                name = 'dipeo'

        return logging.getLogger(name)

    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)

    def log_info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, extra=kwargs)

    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)

    def log_error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)


# Convenience function for module-level logging
def get_module_logger(name: str) -> logging.Logger:
    """Get a logger for module-level usage.

    This is the recommended pattern for module-level logging in DiPeO:

    Example:
        from dipeo.config.base_logger import get_module_logger

        logger = get_module_logger(__name__)
        logger.info("Module loaded")

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)