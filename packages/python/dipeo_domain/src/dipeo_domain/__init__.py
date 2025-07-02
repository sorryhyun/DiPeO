"""
DiPeO Domain Models

This package contains the shared domain models for the DiPeO project.
These models are auto-generated from TypeScript definitions.
"""

__version__ = "0.1.0"

# Import all models
from .models import *  # noqa: F401, F403

# Rebuild models to resolve forward references
from .models import DomainDiagram

DomainDiagram.model_rebuild()
