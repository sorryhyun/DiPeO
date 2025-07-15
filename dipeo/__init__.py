"""
DiPeO - Diagrammed People & Organizations

This is the umbrella package that provides unified access to all DiPeO modules.
It re-exports the core functionality from the various sub-packages for easier imports.

Usage:
    from dipeo import core, domain, diagram, application, infra, container
    from dipeo.models import (Person, Diagram, NodeType)
"""

import warnings
from typing import TYPE_CHECKING

# Version information
__version__ = "0.1.0"

# Import sub-modules
from . import core, diagram, domain
from . import domain as models  # Alias for backward compatibility

# Track what we successfully imported
_imported_modules = ["core", "domain", "models", "diagram"]

# For convenience, re-export commonly used items from core
try:
    from .core import (
        BaseService,
        DiPeOError,
        Error,
        NodeExecutionError,
        Result,
        ValidationError,
    )
    _imported_modules.extend([
        "BaseService", "Result", "Error",
        "DiPeOError", "ValidationError", "NodeExecutionError"
    ])
except ImportError as e:
    warnings.warn(f"Could not import some core items: {e}", ImportWarning)


# For convenience, re-export commonly used models from domain
try:
    from .domain import (
        HandleReference,
        create_handle_id,
        parse_handle_id,
    )
    from .domain.models import (
        Arrow,
        DomainDiagram,
        DomainPerson,
        Edge,
        NodeArrow,
        NodeType,
    )
    # Create aliases for cleaner API
    Person = DomainPerson
    Diagram = DomainDiagram
    
    _imported_modules.extend([
        "DomainPerson", "Person", "DomainDiagram", "Diagram", 
        "NodeType", "Arrow", "Edge", "NodeArrow", 
        "HandleReference", "create_handle_id", "parse_handle_id"
    ])
except ImportError as e:
    warnings.warn(f"Could not import some domain items: {e}", ImportWarning)

# For convenience, re-export commonly used items from diagram
try:
    from .diagram import (
        DiagramConverter,
        FormatStrategy,
        UnifiedDiagramConverter,
        converter_registry,
    )
    _imported_modules.extend([
        "UnifiedDiagramConverter", "DiagramConverter",
        "FormatStrategy", "converter_registry"
    ])
except ImportError as e:
    warnings.warn(f"Could not import some diagram items: {e}", ImportWarning)




# Define __all__ based on what we successfully imported
__all__ = ["__version__"] + _imported_modules