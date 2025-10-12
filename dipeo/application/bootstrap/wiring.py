"""Application-level wiring for services.

This module contains ONLY application-layer wiring logic.
Infrastructure wiring has been moved to the composition root (apps/server/bootstrap.py).
The application layer should not import or create infrastructure services directly.
"""

import logging
from typing import Any

from dipeo.application.registry import ServiceRegistry
from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


def wire_application_services(registry: ServiceRegistry) -> None:
    """Wire application-level services that don't require infrastructure.

    This includes use cases, orchestrators, and other application services
    that depend on domain ports rather than infrastructure implementations.
    """
    from dipeo.application.diagram.wiring import (
        wire_diagram_use_cases,
    )
    from dipeo.application.execution.wiring import wire_execution

    # Wire diagram use cases
    wire_diagram_use_cases(registry)
    logger.info("Wired diagram use cases")

    # Wire execution services (includes conversation repositories)
    wire_execution(registry)
    logger.info("Wired execution services")


def wire_feature_flags(registry: ServiceRegistry, features: list[str]) -> None:
    """Wire optional features based on feature flags.

    Args:
        registry: The service registry
        features: List of enabled feature names
    """
    logger.info(f"Processing feature flags: {features}")

    # Application-level feature flags only
    for feature in features:
        if feature == "advanced_orchestration":
            logger.info("Enabling advanced orchestration features")
            # Wire advanced orchestration features
        elif feature == "experimental_handlers":
            logger.info("Enabling experimental handlers")
            # Wire experimental handlers
