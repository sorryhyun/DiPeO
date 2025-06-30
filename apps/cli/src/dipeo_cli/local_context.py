"""Local application context for CLI execution."""

import logging
import os
from typing import Any

from dipeo_core import (
    BaseService,
    LLMServiceError,
    SupportsAPIKey,
    SupportsDiagram,
    SupportsExecution,
    SupportsFile,
    SupportsLLM,
    SupportsMemory,
    SupportsNotion,
)


class MinimalStateStore:
    """Minimal state store for local execution."""

    async def create_execution_in_cache(self, execution_id: str, diagram_id: str | None, variables: dict):
        """Create execution record (no-op for local execution)."""
        pass

    async def update_node_state(self, execution_id: str, node_id: str, state: str):
        """Update node state (no-op for local execution)."""
        pass


class MinimalMessageRouter:
    """Minimal message router for local execution."""

    async def send_update(self, execution_id: str, update: dict):
        """Send update (no-op for local execution)."""
        pass


logger = logging.getLogger(__name__)


class LLMServiceAdapter:
    """Adapter to make SimpleLLMService work with SimpleConversationService."""
    
    def __init__(self, simple_llm_service):
        self.simple_llm_service = simple_llm_service
    
    async def call_llm(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """Adapt the call to match SimpleConversationService expectations."""
        return await self.simple_llm_service.call_llm(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )


class SimpleLLMService(BaseService):
    """Simple LLM service for local execution that uses environment variables for API keys."""
    
    def __init__(self):
        super().__init__()
        self._api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY"),
            "xai": os.getenv("XAI_API_KEY"),
        }
    
    async def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    async def call_llm(
        self,
        service: str | None = None,
        api_key_id: str = "",
        model: str = "gpt-4.1-nano",
        messages: Any = None,
        system_prompt: str = "",
        **kwargs
    ) -> dict[str, Any]:
        """Call an LLM with the given messages."""
        # Handle both protocol signature and simplified signature
        if isinstance(messages, list) and messages:
            # Already in correct format
            pass
        else:
            # Convert from protocol format if needed
            messages = messages or []
            
        # Extract additional parameters
        temperature = kwargs.get('temperature')
        max_tokens = kwargs.get('max_tokens')
            
        try:
            # Determine provider from model name or service parameter
            if service:
                provider = service.lower()
            else:
                provider = self._get_provider_from_model(model)
            api_key = self._api_keys.get(provider)
            
            if not api_key:
                raise LLMServiceError(
                    service=provider,
                    message=f"API key not found for {provider}. Please set {provider.upper()}_API_KEY environment variable."
                )
            
            # Import the appropriate client based on provider
            if provider == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature or 0.7,
                    max_tokens=max_tokens,
                )
                
                return {
                    "content": response.choices[0].message.content,
                    "role": "assistant",
                    "model": model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    } if response.usage else None
                }
            
            if provider == "anthropic":
                from anthropic import Anthropic
                client = Anthropic(api_key=api_key)
                
                # Convert messages to Anthropic format
                system_message = None
                anthropic_messages = []
                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        anthropic_messages.append(msg)
                
                response = client.messages.create(
                    model=model,
                    messages=anthropic_messages,
                    system=system_message,
                    temperature=temperature or 0.7,
                    max_tokens=max_tokens or 1024,
                )
                
                return {
                    "content": response.content[0].text if response.content else "",
                    "role": "assistant",
                    "model": model,
                    "usage": {
                        "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                        "completion_tokens": response.usage.output_tokens if response.usage else 0,
                        "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
                    } if response.usage else None
                }
            
            raise LLMServiceError(
                service=provider,
                message=f"Provider {provider} not yet implemented in local mode"
            )
                
        except Exception as e:
            logger.error(f"Error calling LLM: {e!s}")
            raise LLMServiceError(service="llm", message=str(e))
    
    def _get_provider_from_model(self, model: str) -> str:
        """Determine provider from model name."""
        model_lower = model.lower()
        
        if "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
            return "openai"
        if "claude" in model_lower:
            return "anthropic"
        if "gemini" in model_lower:
            return "google"
        if "groq" in model_lower or "llama" in model_lower or "mixtral" in model_lower:
            return "groq"
        if "grok" in model_lower:
            return "xai"
        # Default to OpenAI for unknown models
        return "openai"
    
    def get_token_counts(self, client_name: str, usage: Any) -> Any:
        """Get token counts from usage data."""
        # This is a simplified implementation
        return usage
    
    def pre_initialize_model(self, service: str, model: str, api_key_id: str) -> bool:
        """Pre-initialize a model (no-op for local execution)."""
        return True
    
    async def get_available_models(self, service: str, api_key_id: str) -> list[str]:
        """Get available models for a service."""
        # Return a basic list of known models
        if service == "openai":
            return ["gpt-4.1-nano", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]
        if service == "anthropic":
            return ["claude-3-sonnet-20240229", "claude-3-opus-20240229"]
        return []


class LocalAppContext:
    """Minimal application context for CLI local execution."""

    def __init__(self):
        # Required services - will be None for minimal local execution
        self.api_key_service: SupportsAPIKey | None = None
        self.llm_service: SupportsLLM | None = None
        self.file_service: SupportsFile | None = None
        self.memory_service: SupportsMemory | None = None  # Changed from conversation_service
        self.conversation_service: Any | None = None  # Will be SimpleConversationService
        self.execution_service: SupportsExecution | None = None
        self.notion_service: SupportsNotion | None = None
        self.diagram_storage_service: SupportsDiagram | None = None

        # Minimal infrastructure
        self.state_store = MinimalStateStore()
        self.message_router = MinimalMessageRouter()

    async def initialize_for_local(self):
        """Initialize minimal services for local execution."""
        # Import necessary services
        from dipeo_application import LocalExecutionService
        from dipeo_infra import SimpleFileService, SimpleMemoryService

        # Initialize basic services
        simple_llm = SimpleLLMService()
        await simple_llm.initialize()
        self.llm_service = simple_llm
        
        self.memory_service = SimpleMemoryService()
        self.file_service = SimpleFileService()
        
        # TODO: Initialize conversation service when it's updated to use correct domain models
        # For now, we'll use None which means person_job nodes won't work in local mode
        self.conversation_service = None

        # Initialize execution service
        self.execution_service = LocalExecutionService(self)
        await self.execution_service.initialize()
        
        logger.info("Local context initialized with simple services (without conversation service)")
