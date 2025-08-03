"""Domain layer diagram module.

This module contains the core domain models and logic for diagrams:
- models/: ExecutableDiagram and related domain models
- compilation/: Domain-level diagram compilation logic
- strategies/: Format conversion strategies
- services/: Business logic services
"""

from .models import (
    ExecutableDiagram,
    ExecutableNode,
    ExecutableEdgeV2,
    BaseExecutableNode,
    NodeOutputProtocolV2,
)

__all__ = [
    # Models
    "ExecutableDiagram",
    "ExecutableNode", 
    "ExecutableEdgeV2",
    "BaseExecutableNode",
    "NodeOutputProtocolV2",
]