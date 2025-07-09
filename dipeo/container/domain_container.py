"""Domain layer container - Business logic and rules."""

from dependency_injector import containers, providers


def _create_api_key_service():
    from dipeo.domain.services.apikey import APIKeyDomainService

    return APIKeyDomainService()


def _create_api_domain_service():
    """Create pure API domain service."""
    from dipeo.domain.services.api.api_domain_service import APIDomainService
    return APIDomainService()


def _create_file_domain_service():
    """Create pure file domain service."""
    from dipeo.domain.services.file.file_domain_service import FileDomainService
    return FileDomainService()


def _create_text_processing_service():
    from dipeo.domain.services.text import TextProcessingDomainService

    return TextProcessingDomainService()


def _create_template_service():
    from dipeo.domain.services.text.template_service import TemplateService
    
    return TemplateService()


def _create_validation_service():
    from dipeo.domain.services.validation import ValidationDomainService

    return ValidationDomainService()


def _create_arrow_processor():
    from dipeo.domain.services.arrow import ArrowProcessor
    
    return ArrowProcessor()


def _create_memory_transformer():
    from dipeo.domain.services.arrow import MemoryTransformer
    
    return MemoryTransformer()


def _create_flow_control_service():
    from dipeo.domain.services.execution import FlowControlService
    
    return FlowControlService()


def _create_conversation_service(memory_service):
    from dipeo.domain.services.conversation.simple_service import (
        ConversationMemoryService,
    )

    return ConversationMemoryService(memory_service)


def _create_diagram_domain_service():
    from dipeo.domain.services.diagram import DiagramDomainService
    return DiagramDomainService()


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
    from dipeo.domain.services.diagram.domain_service import (
        DiagramStorageDomainService,
    )

    return DiagramStorageDomainService(storage_service=storage_service)


def _create_diagram_validator(api_key_service):
    from dipeo.domain.services.execution.validators import DiagramValidator

    return DiagramValidator(api_key_service)


def _create_db_operations_service(file_service, validation_service):
    from dipeo.domain.services.db import DBOperationsDomainService

    return DBOperationsDomainService(file_service, validation_service)


def _create_condition_evaluation_service(template_service):
    from dipeo.domain.services.condition import ConditionEvaluationService
    
    return ConditionEvaluationService(template_service)


def _create_input_resolution_service(arrow_processor):
    from dipeo.domain.services.execution import InputResolutionService
    
    return InputResolutionService(arrow_processor=arrow_processor)


def _create_person_job_services(template_service, conversation_memory_service, memory_transformer):
    from dipeo.domain.services.person_job import (
        PromptProcessingService,
        ConversationProcessingService,
        PersonJobOutputBuilder,
    )
    
    # Import new focused services
    from dipeo.domain.services.prompt.builder import PromptBuilder
    from dipeo.domain.services.conversation.state_manager import ConversationStateManager
    from dipeo.domain.services.conversation.message_builder import MessageBuilder
    from dipeo.domain.services.llm.executor import LLMExecutor
    from dipeo.domain.services.person_job.orchestrator import PersonJobOrchestrator
    
    # Create services needed by the orchestrator
    prompt_service = PromptProcessingService(template_service)
    conversation_processor = ConversationProcessingService()
    output_builder = PersonJobOutputBuilder()
    
    # Create new focused services
    prompt_builder = PromptBuilder()
    conversation_state_manager = ConversationStateManager()
    message_builder = MessageBuilder()
    llm_executor = LLMExecutor()
    
    # Create orchestrator with new services
    person_job_orchestrator = PersonJobOrchestrator(
        prompt_builder=prompt_builder,
        conversation_state_manager=conversation_state_manager,
        message_builder=message_builder,
        llm_executor=llm_executor,
        output_builder=output_builder,
        conversation_processor=conversation_processor,
        memory_transformer=memory_transformer,
    )
    
    return {
        "prompt_service": prompt_service,
        "conversation_processor": conversation_processor,
        "output_builder": output_builder,
        # New focused services
        "prompt_builder": prompt_builder,
        "conversation_state_manager": conversation_state_manager,
        "message_builder": message_builder,
        "llm_executor": llm_executor,
        "person_job_orchestrator": person_job_orchestrator,
    }


class DomainContainer(containers.DeclarativeContainer):
    """Domain layer container - Business logic and rules."""
    
    config = providers.Configuration()
    base_dir = providers.Configuration()
    infra = providers.DependenciesContainer()
    
    # Core domain services
    api_key_service = providers.Singleton(_create_api_key_service)
    api_domain_service = providers.Singleton(_create_api_domain_service)
    file_domain_service = providers.Singleton(_create_file_domain_service)
    text_processing_service = providers.Singleton(_create_text_processing_service)
    template_service = providers.Singleton(_create_template_service)
    validation_service = providers.Singleton(_create_validation_service)
    arrow_processor = providers.Singleton(_create_arrow_processor)
    memory_transformer = providers.Singleton(_create_memory_transformer)
    flow_control_service = providers.Singleton(_create_flow_control_service)
    
    # Conversation service (depends on infra memory)
    conversation_service = providers.Singleton(
        _create_conversation_service,
        memory_service=infra.memory_service,
    )
    
    # Diagram services
    diagram_domain_service = providers.Singleton(_create_diagram_domain_service)
    diagram_storage_service = providers.Singleton(
        _create_diagram_storage_service,
        base_dir=base_dir,
        diagram_domain_service=diagram_domain_service,
    )
    diagram_storage_adapter = providers.Singleton(
        _create_diagram_storage_adapter,
        storage_service=diagram_storage_service,
        diagram_domain_service=diagram_domain_service,
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
    )