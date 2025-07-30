"""Immutable pure business logic services."""

from dependency_injector import providers

from ..base import ImmutableBaseContainer


def _create_api_business_logic():
    """Create pure API business logic utilities."""
    from dipeo.domain.api.services import APIBusinessLogic
    return APIBusinessLogic()


def _create_file_business_logic():
    """Create pure file business logic utilities."""
    # Removed - old file services are deprecated
    return None


def _create_diagram_business_logic():
    """Create pure diagram business logic utilities."""
    from dipeo.domain.diagram.services import DiagramBusinessLogic
    return DiagramBusinessLogic()



def _create_base_validator():
    """Create base validation service."""
    from dipeo.domain.validators import BaseValidator
    return BaseValidator()


def _create_condition_evaluator():
    """Create condition evaluation service."""
    from dipeo.application.utils import ConditionEvaluator
    return ConditionEvaluator()


def _create_prompt_builder():
    """Create prompt builder service."""
    from dipeo.application.utils import PromptBuilder
    return PromptBuilder()



def _create_validation_service():
    """Create shared validation service."""
    from dipeo.domain.validators import BaseValidator
    return BaseValidator()


def _create_api_validator():
    """Create API validator service."""
    from dipeo.domain.validators import APIValidator
    return APIValidator()


def _create_file_validator():
    """Create file validator service."""
    from dipeo.domain.validators import FileValidator
    return FileValidator()


def _create_db_validator():
    """Create database validator service."""
    from dipeo.domain.validators import DataValidator
    return DataValidator()


def _create_backup_service():
    """Create backup service."""
    # Removed - old file services are deprecated
    return None


def _create_path_validator():
    """Create path validator service."""
    from dipeo.domain.validators import PathValidator
    return PathValidator()


def _create_llm_domain_service():
    """Create LLM domain service."""
    from dipeo.domain.llm import LLMDomainService
    return LLMDomainService()


def _create_execution_validator():
    """Create execution validator."""
    from dipeo.domain.validators import ExecutionValidator
    return ExecutionValidator()


def _create_domain_service_registry():
    """Create domain service registry."""
    from dipeo.domain.service_registry import get_domain_service_registry
    return get_domain_service_registry()


class BusinessLogicContainer(ImmutableBaseContainer):
    """Immutable pure business logic services.
    
    These services contain pure business logic with no I/O operations
    or external dependencies. They are stateless and can be safely shared.
    """
    
    config = providers.Configuration()
    
    # Dependencies from other containers (minimal)
    static = providers.DependenciesContainer()
    
    # Pure business logic services by domain
    # API domain
    api_business_logic = providers.Singleton(_create_api_business_logic)
    api_validator = providers.Singleton(_create_api_validator)
    
    # File domain
    file_business_logic = providers.Singleton(_create_file_business_logic)
    file_validator = providers.Singleton(_create_file_validator)
    backup_service = providers.Singleton(_create_backup_service)
    path_validator = providers.Singleton(_create_path_validator)
    
    # Diagram domain
    diagram_business_logic = providers.Singleton(_create_diagram_business_logic)
    
    # Database domain
    db_validator = providers.Singleton(_create_db_validator)
    
    # Shared services
    base_validator = providers.Singleton(_create_base_validator)
    validation_service = providers.Singleton(_create_validation_service)
    
    # Template and evaluation services
    condition_evaluator = providers.Singleton(_create_condition_evaluator)
    prompt_builder = providers.Singleton(_create_prompt_builder)

    # New domain services (Phase 4 & 5)
    llm_domain_service = providers.Singleton(_create_llm_domain_service)
    execution_validator = providers.Singleton(_create_execution_validator)
    domain_service_registry = providers.Singleton(_create_domain_service_registry)