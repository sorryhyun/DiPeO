"""Immutable services for static analysis, compilation, and validation."""

from dependency_injector import providers

from ..base import ImmutableBaseContainer


def _create_diagram_compiler():
    """Create the static diagram compiler."""
    from dipeo.application.resolution import StaticDiagramCompiler
    return StaticDiagramCompiler()


def _create_node_registry():
    """Create the registry of node handlers."""
    from dipeo.application import get_global_registry
    
    # Return the global handler registry
    return get_global_registry()


def _create_diagram_validator(api_key_service):
    """Create the diagram validator."""
    from dipeo.domain.diagram.services import DiagramValidator
    return DiagramValidator(api_key_service)


def _create_template_processor():
    """Create the template processor."""
    from dipeo.utils.template import TemplateProcessor
    return TemplateProcessor()


def _create_validation_rules():
    """Create the validation rules registry."""
    from dipeo.domain.diagram.services.validation_rules import ValidationRules
    return ValidationRules()


def _create_execution_order_calculator():
    """Create the execution order calculator."""
    from dipeo.application.resolution import ExecutionOrderCalculator
    return ExecutionOrderCalculator()


def _create_arrow_transformer():
    """Create the arrow transformer."""
    from dipeo.application.resolution import ArrowTransformer
    return ArrowTransformer()


def _create_handle_resolver():
    """Create the handle resolver."""
    from dipeo.application.resolution import HandleResolver
    return HandleResolver()


class StaticServicesContainer(ImmutableBaseContainer):
    """Immutable services for static analysis and compilation.
    
    These services align with dipeo/core/static/ and provide
    compilation, validation, and transformation capabilities.
    All services are stateless and can be safely shared.
    """
    
    config = providers.Configuration()
    
    # Dependencies from other containers
    persistence = providers.DependenciesContainer()
    
    # Compilation and resolution services
    diagram_compiler = providers.Singleton(_create_diagram_compiler)
    
    # Node registry - provides handlers for different node types
    node_registry = providers.Singleton(_create_node_registry)
    
    # Validation services
    diagram_validator = providers.Singleton(
        _create_diagram_validator,
        api_key_service=persistence.api_key_service,
    )
    
    validation_rules = providers.Singleton(_create_validation_rules)
    
    # Transformation services
    template_processor = providers.Singleton(_create_template_processor)
    
    # Diagram resolution services
    execution_order_calculator = providers.Singleton(_create_execution_order_calculator)
    arrow_transformer = providers.Singleton(_create_arrow_transformer)
    handle_resolver = providers.Singleton(_create_handle_resolver)