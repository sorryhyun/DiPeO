"""
DiPeO - Diagrammed People & Organizations

This is the umbrella package that provides unified access to all DiPeO modules.
It re-exports the core functionality from the various sub-packages for easier imports.

Usage:
    from dipeo import core, domain, application, infra, container
    from dipeo.diagram_generated import (Person, Diagram, NodeType)
"""

import warnings
from typing import TYPE_CHECKING

# Version information
__version__ = "0.1.0"

# Import sub-modules
from . import domain
from . import domain as models  # Alias for backward compatibility

# Track what we successfully imported
_imported_modules = ["domain", "models"]

# For convenience, re-export commonly used items from domain base
try:
    from .domain.base.exceptions import (
        DiPeOError,
        NodeExecutionError,
        ValidationError,
    )
    from .domain.base.service import BaseService
    from .domain.type_defs import Error, Result

    _imported_modules.extend(
        ["BaseService", "Result", "Error", "DiPeOError", "ValidationError", "NodeExecutionError"]
    )
except ImportError as e:
    warnings.warn(f"Could not import some domain base items: {e}", ImportWarning, stacklevel=2)


# For convenience, re-export commonly used models from domain
try:
    from .diagram_generated import (
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

    _imported_modules.extend(
        [
            "DomainPerson",
            "Person",
            "DomainDiagram",
            "Diagram",
            "NodeType",
            "Arrow",
            "Edge",
            "NodeArrow",
            "HandleReference",
            "create_handle_id",
            "parse_handle_id",
        ]
    )
except ImportError as e:
    warnings.warn(f"Could not import some domain items: {e}", ImportWarning, stacklevel=2)

# For convenience, re-export commonly used items from diagram ports
try:
    from .domain.diagram.ports import DiagramStorageSerializer as DiagramConverter
    from .domain.diagram.ports import FormatStrategy

    _imported_modules.extend(["DiagramConverter", "FormatStrategy"])
except ImportError as e:
    warnings.warn(f"Could not import some diagram items: {e}", ImportWarning, stacklevel=2)


# Define __all__ based on what we successfully imported
__all__ = ["__version__", *_imported_modules]
