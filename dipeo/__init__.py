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
from . import core
from . import domain
from . import domain as models  # Alias for backward compatibility
from . import diagram
from . import application
from . import infra
from . import container

# Track what we successfully imported
_imported_modules = ["core", "domain", "models", "diagram", "application", "infra", "container"]

# For convenience, re-export commonly used items from core
try:
    from .core import (
        BaseService,
        BaseExecutor,
        BaseNodeHandler,
        ExecutionOptions,
        NodeDefinition,
        NodeHandler,
        Result,
        Error,
        DiPeOError,
        ValidationError,
        NodeExecutionError,
    )
    _imported_modules.extend([
        "BaseService", "BaseExecutor", "BaseNodeHandler",
        "ExecutionOptions",
        "NodeDefinition", "NodeHandler", "Result", "Error",
        "DiPeOError", "ValidationError", "NodeExecutionError"
    ])
except ImportError as e:
    warnings.warn(f"Could not import some core items: {e}", ImportWarning)

# For convenience, re-export commonly used models from domain
try:
    from .domain.models import (
        DomainPerson,
        DomainDiagram,
        NodeType,
        Arrow,
        Edge,
        NodeArrow,
    )
    from .domain import (
        HandleReference,
        create_handle_id,
        parse_handle_id,
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
        UnifiedDiagramConverter,
        DiagramConverter,
        FormatStrategy,
        converter_registry,
    )
    _imported_modules.extend([
        "UnifiedDiagramConverter", "DiagramConverter",
        "FormatStrategy", "converter_registry"
    ])
except ImportError as e:
    warnings.warn(f"Could not import some diagram items: {e}", ImportWarning)

# For convenience, re-export commonly used items from application
try:
    from .application import (
        StatefulExecutionEngine,
        UnifiedServiceRegistry,
    )
    _imported_modules.extend([
        "StatefulExecutionEngine",
        "UnifiedServiceRegistry"
    ])
except ImportError as e:
    warnings.warn(f"Could not import some application items: {e}", ImportWarning)

# For convenience, re-export commonly used items from infra
try:
    from .infra import (
        LLMInfraService,
        ModularFileService,
        AsyncFileAdapter,
    )
    
    _imported_modules.extend([
        "LLMInfraService", "ModularFileService", "AsyncFileAdapter"
    ])
except ImportError as e:
    warnings.warn(f"Could not import some infra items: {e}", ImportWarning)

# For convenience, re-export commonly used items from container
try:
    from .container import (
        Container,
        init_resources,
        shutdown_resources,
    )
    _imported_modules.extend([
        "Container", "init_resources", "shutdown_resources"
    ])
except ImportError as e:
    warnings.warn(f"Could not import some container items: {e}", ImportWarning)

# Define __all__ based on what we successfully imported
__all__ = ["__version__"] + _imported_modules