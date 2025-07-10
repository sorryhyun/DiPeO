"""Domain layer container - Business logic and rules."""

from dependency_injector import containers, providers


def _create_api_key_service(storage):
    from dipeo.application.services.apikey import APIKeyService

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
    from dipeo.utils.text.template_service import TemplateService
    
    return TemplateService()


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


def _create_conversation_manager(memory_service):
    from dipeo.application.services.conversation.conversation_manager_impl import ConversationManagerImpl
    
    return ConversationManagerImpl(memory_service)


def _create_conversation_service(memory_service, conversation_manager=None):
    from dipeo.application.services.conversation.memory_service_v2 import ConversationMemoryServiceV2

    return ConversationMemoryServiceV2(memory_service, conversation_manager)


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
    from dipeo.application.services.diagram import DiagramService

    return DiagramService(storage_service=storage_service)


def _create_diagram_validator(api_key_service):
    from dipeo.application.execution.validators import DiagramValidator

    return DiagramValidator(api_key_service)


def _create_db_operations_service(file_service, validation_service):
    from dipeo.infra.database import DBOperationsDomainService

    return DBOperationsDomainService(file_service, validation_service)


def _create_condition_evaluation_service(template_service):
    from dipeo.application.execution.condition import ConditionEvaluationService
    
    return ConditionEvaluationService(template_service)


def _create_input_resolution_service(arrow_processor):
    from dipeo.application.execution.input import InputResolutionService
    
    return InputResolutionService(arrow_processor=arrow_processor)


def _create_person_job_services(template_service, conversation_memory_service, memory_transformer, conversation_manager=None):
    from dipeo.application.execution.person_job import (
        PromptProcessingService,
        ConversationProcessingService,
        PersonJobOutputBuilder,
    )
    
    # Import new focused services
    from dipeo.utils.prompt import PromptBuilder
    from dipeo.utils.conversation.state_utils import ConversationStateManager
    from dipeo.application.services.llm import LLMExecutor
    from dipeo.application.execution.person_job.orchestrator_v2 import PersonJobOrchestratorV2
    
    # Create services needed by the orchestrator
    prompt_service = PromptProcessingService(template_service)
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
        template_service=template_service,
        conversation_manager=conversation_manager,
    )
    
    return {
        "prompt_service": prompt_service,
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
    
    # Conversation manager (new protocol implementation)
    conversation_manager = providers.Singleton(
        _create_conversation_manager,
        memory_service=infra.memory_service,
    )
    
    # Conversation service (depends on infra memory and conversation manager)
    conversation_service = providers.Singleton(
        _create_conversation_service,
        memory_service=infra.memory_service,
        conversation_manager=conversation_manager,
    )
    
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
        template_service=template_service,
    )
    
    # Input resolution
    input_resolution_service = providers.Singleton(
        _create_input_resolution_service,
        arrow_processor=arrow_processor,
    )
    
    # Person job services
    person_job_services = providers.Singleton(
        _create_person_job_services,
        template_service=template_service,
        conversation_memory_service=conversation_service,
        memory_transformer=memory_transformer,
        conversation_manager=conversation_manager,
    )