"""Immutable pure business logic services."""

from dependency_injector import containers, providers
from ..base import ImmutableBaseContainer


def _create_api_business_logic():
    """Create pure API business logic utilities."""
    from dipeo.domain.api.services import APIBusinessLogic
    return APIBusinessLogic()


def _create_file_business_logic():
    """Create pure file business logic utilities."""
    from dipeo.domain.file.services import FileBusinessLogic
    return FileBusinessLogic()


def _create_diagram_business_logic():
    """Create pure diagram business logic utilities."""
    from dipeo.domain.diagram.services import DiagramBusinessLogic
    return DiagramBusinessLogic()


def _create_text_processing_service():
    """Create text processing domain service."""
    from dipeo.utils.text import TextProcessingDomainService
    return TextProcessingDomainService()


def _create_base_validator():
    """Create base validation service."""
    from dipeo.core.base import BaseValidator
    return BaseValidator()


def _create_condition_evaluator():
    """Create condition evaluation service."""
    from dipeo.application.utils.template import ConditionEvaluator
    return ConditionEvaluator()


def _create_prompt_builder():
    """Create prompt builder service."""
    from dipeo.application.utils.template import PromptBuilder
    return PromptBuilder()


def _create_input_resolution_service(arrow_processor):
    """Create input resolution service."""
    from dipeo.application.execution.input import InputResolutionService
    return InputResolutionService(arrow_processor=arrow_processor)


def _create_conversation_processor():
    """Create conversation processing service."""
    from dipeo.application.execution.person_job import ConversationProcessingService
    return ConversationProcessingService()


def _create_output_builder():
    """Create person job output builder."""
    from dipeo.application.execution.person_job import PersonJobOutputBuilder
    return PersonJobOutputBuilder()


def _create_conversation_state_manager():
    """Create conversation state manager."""
    from dipeo.domain.conversation.services import ConversationStateManager
    return ConversationStateManager()


def _create_message_formatter():
    """Create message formatter service."""
    from dipeo.domain.conversation.services import MessageFormatter
    return MessageFormatter()


def _create_memory_strategy_factory():
    """Create memory strategy factory."""
    from dipeo.domain.conversation.services.memory_strategies import MemoryStrategyFactory
    return MemoryStrategyFactory()


def _create_diagram_analyzer():
    """Create diagram analyzer service."""
    from dipeo.domain.diagram.services import DiagramAnalyzer
    return DiagramAnalyzer()


def _create_diagram_transformer():
    """Create diagram transformer service."""
    from dipeo.domain.diagram.services import DiagramTransformer
    return DiagramTransformer()


def _create_validation_service():
    """Create shared validation service."""
    from dipeo.core.base import BaseValidator
    return BaseValidator()


def _create_api_validator():
    """Create API validator service."""
    from dipeo.domain.api.services import APIValidator
    return APIValidator()


def _create_file_validator():
    """Create file validator service."""
    from dipeo.domain.file.services import FileValidator
    return FileValidator()


def _create_db_validator():
    """Create database validator service."""
    from dipeo.domain.db.services import DBValidator
    return DBValidator()


def _create_backup_service():
    """Create backup service."""
    from dipeo.domain.file.services import BackupService
    return BackupService()


def _create_path_validator():
    """Create path validator service."""
    from dipeo.domain.file.services import PathValidator
    return PathValidator()


def _create_data_transformer():
    """Create data transformer service."""
    from dipeo.domain.services.integration import DataTransformer
    return DataTransformer()


def _create_llm_domain_service():
    """Create LLM domain service."""
    from dipeo.domain.llm import LLMDomainService
    return LLMDomainService()


def _create_execution_domain_service():
    """Create execution domain service."""
    from dipeo.domain.execution import ExecutionDomainService
    return ExecutionDomainService()


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
    diagram_analyzer = providers.Singleton(_create_diagram_analyzer)
    diagram_transformer = providers.Singleton(_create_diagram_transformer)
    
    # Database domain
    db_validator = providers.Singleton(_create_db_validator)
    
    # Shared services
    text_processing_service = providers.Singleton(_create_text_processing_service)
    base_validator = providers.Singleton(_create_base_validator)
    validation_service = providers.Singleton(_create_validation_service)
    
    # Template and evaluation services
    condition_evaluator = providers.Singleton(_create_condition_evaluator)
    prompt_builder = providers.Singleton(_create_prompt_builder)
    
    # Execution services (pure logic only)
    input_resolution_service = providers.Singleton(
        _create_input_resolution_service,
        arrow_processor=static.arrow_processor,
    )
    
    # Person job services (pure processing logic)
    conversation_processor = providers.Singleton(_create_conversation_processor)
    output_builder = providers.Singleton(_create_output_builder)
    
    # Conversation domain
    conversation_state_manager = providers.Singleton(_create_conversation_state_manager)
    message_formatter = providers.Singleton(_create_message_formatter)
    memory_strategy_factory = providers.Singleton(_create_memory_strategy_factory)
    
    # Integration services
    data_transformer = providers.Singleton(_create_data_transformer)
    
    # New domain services (Phase 4 & 5)
    llm_domain_service = providers.Singleton(_create_llm_domain_service)
    execution_domain_service = providers.Singleton(_create_execution_domain_service)
    domain_service_registry = providers.Singleton(_create_domain_service_registry)