"""Mutable services for external integrations."""

from dependency_injector import providers

from ..base import MutableBaseContainer


def _create_llm_service(api_key_service, llm_domain_service):
    """Create LLM infrastructure service."""
    from dipeo.infra.llm import LLMInfraService
    
    return LLMInfraService(api_key_service, llm_domain_service)


def _create_notion_service():
    """Create Notion integration service."""
    from dipeo.infra.adapters.notion import NotionAPIService
    return NotionAPIService()


def _create_api_service(api_business_logic, file_service):
    """Create infrastructure API service."""
    from dipeo.infra.services.api import APIService
    return APIService(
        business_logic=api_business_logic,
        file_service=file_service
    )


def _create_integrated_diagram_service(file_repository, loader_adapter):
    """Create integrated diagram service with conversion capabilities."""
    from dipeo.infra.diagram.integrated_diagram_service import IntegratedDiagramService
    return IntegratedDiagramService(
        file_repository=file_repository,
        loader_adapter=loader_adapter
    )


def _create_openai_adapter():
    """Create OpenAI LLM adapter."""
    from dipeo.infra.llm.adapters import ChatGPTAdapter
    return ChatGPTAdapter()


def _create_claude_adapter():
    """Create Claude LLM adapter."""
    from dipeo.infra.llm.adapters import ClaudeAdapter
    return ClaudeAdapter()


def _create_gemini_adapter():
    """Create Gemini LLM adapter."""
    from dipeo.infra.llm.adapters import GeminiAdapter
    return GeminiAdapter()


def _create_llm_factory():
    """Create LLM factory with all adapters."""
    # TODO: LLMFactory not yet implemented
    # For now, return None as it's not used
    return None


def _create_webhook_service():
    """Create webhook service for external notifications."""
    # TODO: Implement webhook service
    return None


def _create_email_service():
    """Create email service for notifications."""
    # TODO: Implement email service
    return None


class IntegrationServicesContainer(MutableBaseContainer):
    """Mutable services for external integrations.
    
    These services handle communication with external systems like
    LLMs, Notion, APIs, webhooks, etc. They maintain connection state
    and should handle retries, rate limiting, and error recovery.
    """
    
    config = providers.Configuration()
    base_dir = providers.Configuration()
    
    # Dependencies from other containers
    business = providers.DependenciesContainer()
    persistence = providers.DependenciesContainer()
    
    # LLM services and adapters
    openai_adapter = providers.Singleton(_create_openai_adapter)
    claude_adapter = providers.Singleton(_create_claude_adapter)
    gemini_adapter = providers.Singleton(_create_gemini_adapter)
    
    llm_factory = providers.Singleton(_create_llm_factory)
    
    llm_service = providers.Singleton(
        _create_llm_service,
        api_key_service=persistence.api_key_service,
        llm_domain_service=business.llm_domain_service,
    )
    
    # External API integrations
    notion_service = providers.Singleton(_create_notion_service)
    
    api_service = providers.Singleton(
        _create_api_service,
        api_business_logic=business.api_business_logic,
        file_service=persistence.file_service,
    )
    
    # Diagram integration service
    integrated_diagram_service = providers.Singleton(
        _create_integrated_diagram_service,
        file_repository=persistence.diagram_storage_service,
        loader_adapter=persistence.diagram_loader,
    )
    
    # Future integrations
    webhook_service = providers.Singleton(_create_webhook_service)
    email_service = providers.Singleton(_create_email_service)