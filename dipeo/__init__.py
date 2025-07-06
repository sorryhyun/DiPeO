"""
DiPeO - Diagrammed People & Organizations

This is the umbrella package that provides unified access to all DiPeO modules.
It re-exports the core functionality from the various sub-packages for easier imports.

Usage:
    from dipeo import core, domain, diagram, application, infra, container
    from dipeo.core import BaseService, UnifiedExecutionContext
    from dipeo.domain import Person, Diagram, NodeType
"""

import warnings
from typing import TYPE_CHECKING

# Version information
__version__ = "0.1.0"

# Track what we successfully imported
_imported_modules = []

# Import sub-modules as namespaces
try:
    # Import from new location
    from . import core
    _imported_modules.append("core")
except ImportError:
    # Fall back to old location with deprecation warning
    try:
        import dipeo_core as core
        _imported_modules.append("core")
        warnings.warn("Using legacy import 'dipeo_core'. Please migrate to 'dipeo.core'.", DeprecationWarning)
    except ImportError:
        core = None
        warnings.warn("dipeo.core not available. Ensure dipeo package is properly set up.", ImportWarning)

try:
    # Import from new location
    from . import domain
    from . import domain as models  # Alias for backward compatibility
    _imported_modules.extend(["domain", "models"])
except ImportError:
    # Fall back to old location with deprecation warning
    try:
        import dipeo_domain as domain
        import dipeo_domain as models  # Alias for backward compatibility
        _imported_modules.extend(["domain", "models"])
    except ImportError:
        domain = None
        models = None
        warnings.warn("dipeo.domain not available. Ensure dipeo package is properly set up.", ImportWarning)

try:
    # Import from new location
    from . import diagram
    _imported_modules.append("diagram")
except ImportError:
    # Fall back to old location with deprecation warning
    try:
        import dipeo_diagram as diagram
        _imported_modules.append("diagram")
        warnings.warn("Using legacy import 'dipeo_diagram'. Please migrate to 'dipeo.diagram'.", DeprecationWarning)
    except ImportError:
        diagram = None
        warnings.warn("dipeo.diagram not available. Ensure dipeo package is properly set up.", ImportWarning)

try:
    # Import from new location
    from . import application
    _imported_modules.append("application")
except ImportError:
    # Fall back to old location with deprecation warning
    try:
        import dipeo_application as application
        _imported_modules.append("application")
        warnings.warn("Using legacy import 'dipeo_application'. Please migrate to 'dipeo.application'.", DeprecationWarning)
    except ImportError:
        application = None
        warnings.warn("dipeo.application not available. Ensure dipeo package is properly set up.", ImportWarning)

try:
    # Import from new location
    from . import infra
    _imported_modules.append("infra")
except ImportError:
    # Fall back to old location with deprecation warning
    try:
        import dipeo_infra as infra
        _imported_modules.append("infra")
        warnings.warn("Using legacy import 'dipeo_infra'. Please migrate to 'dipeo.infra'.", DeprecationWarning)
    except ImportError:
        infra = None
        warnings.warn("dipeo.infra not available. Ensure dipeo package is properly set up.", ImportWarning)

try:
    # Import from new location
    from . import container
    _imported_modules.append("container")
except ImportError:
    # Fall back to old location with deprecation warning
    try:
        import dipeo_container as container
        _imported_modules.append("container")
        warnings.warn("Using legacy import 'dipeo_container'. Please migrate to 'dipeo.container'.", DeprecationWarning)
    except ImportError:
        container = None
        warnings.warn("dipeo.container not available. Ensure dipeo package is properly set up.", ImportWarning)

# For convenience, re-export commonly used items from core
if core is not None:
    try:
        from .core import (
            BaseService,
            BaseExecutor,
            BaseNodeHandler,
            UnifiedExecutionContext,
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
            "UnifiedExecutionContext", "ExecutionOptions", 
            "NodeDefinition", "NodeHandler", "Result", "Error",
            "DiPeOError", "ValidationError", "NodeExecutionError"
        ])
    except ImportError as e:
        warnings.warn(f"Could not import some core items: {e}", ImportWarning)

# For convenience, re-export commonly used models from domain
if domain is not None:
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
        # Try old location as fallback
        try:
            from dipeo_domain.models import (
                DomainPerson,
                DomainDiagram,
                NodeType,
                Arrow,
                Edge,
                NodeArrow,
            )
            from dipeo_domain import (
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
        except ImportError:
            warnings.warn(f"Could not import some domain items: {e}", ImportWarning)
            # Define as None to avoid NameError
            DomainPerson = None
            DomainDiagram = None
            Person = None
            Diagram = None

# For convenience, re-export commonly used items from diagram
if diagram is not None:
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
if application is not None:
    try:
        from .application import (
            ApplicationContext,
            ExecutionEngine,
            LocalExecutionService,
            UnifiedServiceRegistry,
        )
        _imported_modules.extend([
            "ApplicationContext", "ExecutionEngine",
            "LocalExecutionService", "UnifiedServiceRegistry"
        ])
    except ImportError:
        # Try old location as fallback
        try:
            from dipeo_application import (
                ApplicationContext,
                ExecutionEngine,
                LocalExecutionService,
                UnifiedServiceRegistry,
            )
            _imported_modules.extend([
                "ApplicationContext", "ExecutionEngine",
                "LocalExecutionService", "UnifiedServiceRegistry"
            ])
        except ImportError as e:
            warnings.warn(f"Could not import some application items: {e}", ImportWarning)

# For convenience, re-export commonly used items from infra
if infra is not None:
    try:
        from .infra import (
            LLMInfraService,
            ModularFileService,
            AsyncFileAdapter,
            MemoryService,
        )
        # Create alias for backward compatibility
        ConsolidatedFileService = ModularFileService
        
        _imported_modules.extend([
            "LLMInfraService", "ModularFileService", "AsyncFileAdapter",
            "MemoryService", "ConsolidatedFileService"
        ])
    except ImportError:
        # Try old location as fallback
        try:
            from dipeo_infra import (
                ConsolidatedFileService,
                MemoryService,
                LLMInfraService,
                Settings,
                settings,
            )
            _imported_modules.extend([
                "ConsolidatedFileService", "MemoryService",
                "LLMInfraService", "Settings", "settings"
            ])
        except ImportError as e:
            warnings.warn(f"Could not import some infra items: {e}", ImportWarning)

# For convenience, re-export commonly used items from container
if container is not None:
    try:
        from .container import (
            Container,
            init_resources,
            shutdown_resources,
        )
        _imported_modules.extend([
            "Container", "init_resources", "shutdown_resources"
        ])
    except ImportError:
        # Try old location as fallback
        try:
            from dipeo_container import (
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