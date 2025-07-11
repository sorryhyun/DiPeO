"""Domain layer container - Business logic and rules."""

from dependency_injector import containers, providers


def _create_api_key_service(storage):
    from dipeo.application.services.apikey_service import APIKeyService

    return APIKeyService(storage=storage)


def _create_api_business_logic():
    """Create pure API business logic utilities."""
    from dipeo.utils.api import APIBusinessLogic
    return APIBusinessLogic()


def _create_file_business_logic():
    """Create pure file business logic utilities."""
    from dipeo.utils.file import FileBusinessLogic
    return FileBusinessLogic()


def _create_text_processing_service():
    from dipeo.utils.text import TextProcessingDomainService

    return TextProcessingDomainService()


def _create_template_service():
    from dipeo.utils.template import TemplateProcessor
    
    return TemplateProcessor()


def _create_validation_service():
    from dipeo.utils.validation import ValidationDomainService

    return ValidationDomainService()


def _create_arrow_processor():
    from dipeo.utils.arrow import ArrowProcessor
    
    return ArrowProcessor()


def _create_memory_transformer():
    from dipeo.utils.arrow import MemoryTransformer
    
    return MemoryTransformer()


def _create_flow_control_service():
    from dipeo.application.execution.flow_control_service import FlowControlService
    
    return FlowControlService()


def _create_conversation_manager():
    from dipeo.application.services.conversation_manager_impl import (
        ConversationManagerImpl,
    )
    
    return ConversationManagerImpl()


def _create_diagram_business_logic():
    from dipeo.utils.diagram import DiagramBusinessLogic
    return DiagramBusinessLogic()


def _create_diagram_storage_service(base_dir, diagram_domain_service):
    from dipeo.infra.persistence.diagram import DiagramFileRepository
    return DiagramFileRepository(
        domain_service=diagram_domain_service,
        base_dir=base_dir
    )


def _create_diagram_storage_adapter(storage_service, diagram_domain_service):
    from dipeo.infra.persistence.diagram import DiagramStorageAdapter

    return DiagramStorageAdapter(
        file_repository=storage_service,
        domain_service=diagram_domain_service
    )


def _create_diagram_storage_domain_service(storage_service):
    from dipeo.application.services.diagram_service import DiagramService

    return DiagramService(storage_service=storage_service)


def _create_diagram_validator(api_key_service):
    from dipeo.application.execution.validators import DiagramValidator

    return DiagramValidator(api_key_service)


def _create_db_operations_service(file_service, validation_service):
    from dipeo.infra.database import DBOperationsDomainService

    return DBOperationsDomainService(file_service, validation_service)


def _create_condition_evaluation_service():
    from dipeo.application.utils.template import ConditionEvaluator
    
    return ConditionEvaluator()


def _create_input_resolution_service(arrow_processor):
    from dipeo.application.execution.input import InputResolutionService
    
    return InputResolutionService(arrow_processor=arrow_processor)


def _create_person_job_services(memory_transformer, conversation_manager=None):
    from dipeo.application.execution.person_job import (
        ConversationProcessingService,
        PersonJobOutputBuilder,
    )
    from dipeo.application.execution.person_job.orchestrator_v2 import PersonJobOrchestratorV2
    from dipeo.application.services.llm_executor import LLMExecutor

    # Import new focused services
    from dipeo.application.utils.template import PromptBuilder
    from dipeo.utils.conversation.state_utils import ConversationStateManager
    
    # Create services needed by the orchestrator
    conversation_processor = ConversationProcessingService()
    output_builder = PersonJobOutputBuilder()
    
    # Create new focused services
    prompt_builder = PromptBuilder()
    conversation_state_manager = ConversationStateManager()
    llm_executor = LLMExecutor()
    
    # Create enhanced orchestrator with conversation manager
    person_job_orchestrator = PersonJobOrchestratorV2(
        prompt_builder=prompt_builder,
        conversation_state_manager=conversation_state_manager,
        llm_executor=llm_executor,
        output_builder=output_builder,
        conversation_processor=conversation_processor,
        memory_transformer=memory_transformer,
        conversation_manager=conversation_manager,
    )
    
    return {
        "conversation_processor": conversation_processor,
        "output_builder": output_builder,
        # New focused services
        "prompt_builder": prompt_builder,
        "conversation_state_manager": conversation_state_manager,
        "llm_executor": llm_executor,
        "person_job_orchestrator": person_job_orchestrator,
    }


class DomainContainer(containers.DeclarativeContainer):
    """Domain layer container - Business logic and rules."""
    
    config = providers.Configuration()
    base_dir = providers.Configuration()
    infra = providers.DependenciesContainer()
    
    # Core domain services
    api_key_service = providers.Singleton(
        _create_api_key_service,
        storage=infra.api_key_storage,
    )
    api_business_logic = providers.Singleton(_create_api_business_logic)
    file_business_logic = providers.Singleton(_create_file_business_logic)
    text_processing_service = providers.Singleton(_create_text_processing_service)
    template_service = providers.Singleton(_create_template_service)
    validation_service = providers.Singleton(_create_validation_service)
    arrow_processor = providers.Singleton(_create_arrow_processor)
    memory_transformer = providers.Singleton(_create_memory_transformer)
    flow_control_service = providers.Singleton(_create_flow_control_service)
    
    # Conversation service - implements ConversationManager
    conversation_service = providers.Singleton(
        _create_conversation_manager,
    )
    
    # Alias for backward compatibility
    conversation_manager = conversation_service
    
    # Diagram services
    diagram_business_logic = providers.Singleton(_create_diagram_business_logic)
    diagram_storage_service = providers.Singleton(
        _create_diagram_storage_service,
        base_dir=base_dir,
        diagram_domain_service=diagram_business_logic,
    )
    diagram_storage_adapter = providers.Singleton(
        _create_diagram_storage_adapter,
        storage_service=diagram_storage_service,
        diagram_domain_service=diagram_business_logic,
    )
    diagram_storage_domain_service = providers.Singleton(
        _create_diagram_storage_domain_service,
        storage_service=diagram_storage_service,
    )
    diagram_validator = providers.Factory(
        _create_diagram_validator,
        api_key_service=api_key_service,
    )
    
    # DB operations (depends on infra file service)
    db_operations_service = providers.Singleton(
        _create_db_operations_service,
        file_service=infra.file_service,
        validation_service=validation_service,
    )
    
    # Condition evaluation
    condition_evaluation_service = providers.Singleton(
        _create_condition_evaluation_service,
    )
    
    # Input resolution
    input_resolution_service = providers.Singleton(
        _create_input_resolution_service,
        arrow_processor=arrow_processor,
    )
    
    # Person job services
    person_job_services = providers.Singleton(
        _create_person_job_services,
        memory_transformer=memory_transformer,
        conversation_manager=conversation_manager,
    )