"""Ollama adapter implementation for local model execution."""

import logging
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from dipeo.diagram_generated import Message, ToolConfig

from ...capabilities import (
    RetryHandler,
    StreamingHandler,
)
from ...core.adapter import UnifiedAdapter
from ...core.types import (
    AdapterConfig,
    ExecutionPhase,
    LLMResponse,
    ProviderCapabilities,
    ProviderType,
    RetryConfig,
    StreamConfig,
    StreamingMode,
)
from ...processors import MessageProcessor, ResponseProcessor, TokenCounter
from .client import AsyncOllamaClientWrapper, OllamaClientWrapper

logger = logging.getLogger(__name__)


class OllamaAdapter(UnifiedAdapter):
    """Unified Ollama adapter for local model execution."""
    
    def __init__(self, config: AdapterConfig):
        """Initialize Ollama adapter with capabilities."""
        # Set defaults for Ollama
        if not config.api_key:
            config.api_key = ""
        if not config.base_url:
            config.base_url = "http://localhost:11434"
        
        super().__init__(config)
        
        # Initialize limited capabilities for Ollama
        self.retry_handler = RetryHandler(
            ProviderType.OLLAMA,
            RetryConfig(
                max_attempts=config.max_retries or 3,
                initial_delay=config.retry_delay or 1.0,
                backoff_factor=config.retry_backoff or 2.0
            )
        )
        self.streaming_handler = StreamingHandler(
            ProviderType.OLLAMA,
            StreamConfig(mode=config.streaming_mode or StreamingMode.SSE)
        )
        
        # Initialize processors
        self.message_processor = MessageProcessor(ProviderType.OLLAMA)
        self.response_processor = ResponseProcessor(ProviderType.OLLAMA)
        self.token_counter = TokenCounter(ProviderType.OLLAMA)
        
        # Initialize clients
        self.sync_client_wrapper = OllamaClientWrapper(config)
        self.async_client_wrapper = AsyncOllamaClientWrapper(config)
    
    def _get_capabilities(self) -> ProviderCapabilities:
        """Get Ollama provider capabilities."""
        return ProviderCapabilities(
            supports_async=True,
            supports_streaming=True,
            supports_tools=False,  # Ollama doesn't support function calling yet
            supports_structured_output=False,
            supports_vision=True,  # Some models like llava support vision
            supports_web_search=False,
            supports_image_generation=False,
            supports_computer_use=False,
            max_context_length=128000,  # Varies by model
            max_output_tokens=4096,  # Varies by model
            supported_models={
                # Popular Ollama models
                "llama3.3",
                "llama3.2",
                "llama3.1",
                "llama3",
                "llama2",
                "mistral",
                "mixtral",
                "gemma",
                "gemma2",
                "phi",
                "phi3",
                "qwen",
                "qwen2",
                "vicuna",
                "orca",
                "neural-chat",
                "starling",
                "codellama",
                "deepseek-coder",
                "llava",  # Vision model
                "bakllava",  # Vision model
            },
            streaming_modes={StreamingMode.SSE}
        )
    
    def _create_sync_client(self):
        """Create synchronous client."""
        return self.sync_client_wrapper
    
    async def _create_async_client(self):
        """Create asynchronous client."""
        return self.async_client_wrapper
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is supported."""
        # Ollama can pull any model, so we're more permissive
        # Check if it's a known model or follows Ollama naming pattern
        model_base = model.split(":")[0]
        return (
            model_base in self.capabilities.supported_models or
            model in self.capabilities.supported_models or
            True  # Allow any model name as Ollama can pull models dynamically
        )
    
    def prepare_messages(self, messages: List[Message]) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Prepare messages for Ollama API, extracting system prompt."""
        # Extract system prompt
        system_prompt = self.message_processor.extract_system_prompt(messages)
        
        # Filter out system messages and process the rest
        non_system_messages = [msg for msg in messages if msg.role != "system"]
        prepared_messages = self.message_processor.prepare_messages(non_system_messages)
        
        return prepared_messages, system_prompt
    
    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolConfig]] = None,
        response_format: Optional[Any] = None,
        execution_phase: Optional[ExecutionPhase] = None,
        **kwargs
    ) -> LLMResponse:
        """Execute synchronous chat completion with retry logic."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        
        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)
        
        # Ollama doesn't support tools
        if tools:
            logger.warning("Ollama doesn't support function calling/tools yet")
        
        # Execute with retry
        @self.retry_handler.with_retry
        def _execute():
            return self.sync_client_wrapper.chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_prompt,
                **kwargs
            )
        
        raw_response = _execute()
        
        # Process response
        text = ""
        if isinstance(raw_response, dict):
            # Extract text from Ollama response
            if "message" in raw_response:
                text = raw_response["message"].get("content", "")
            elif "response" in raw_response:
                text = raw_response["response"]
        
        # Extract token usage if available
        token_usage = None
        if isinstance(raw_response, dict):
            # Ollama provides eval_count and prompt_eval_count
            prompt_tokens = raw_response.get("prompt_eval_count", 0)
            completion_tokens = raw_response.get("eval_count", 0)
            if prompt_tokens or completion_tokens:
                token_usage = self.token_counter.extract_token_usage(
                    {
                        "prompt_eval_count": prompt_tokens,
                        "eval_count": completion_tokens,
                        "total_count": prompt_tokens + completion_tokens
                    },
                    self.model
                )
        
        response = LLMResponse(
            text=text,
            raw_response=raw_response,
            token_usage=token_usage
        )
        
        return response
    
    async def async_chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolConfig]] = None,
        response_format: Optional[Any] = None,
        execution_phase: Optional[ExecutionPhase] = None,
        **kwargs
    ) -> LLMResponse:
        """Execute asynchronous chat completion with retry logic."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        
        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)
        
        # Ollama doesn't support tools
        if tools:
            logger.warning("Ollama doesn't support function calling/tools yet")
        
        # Execute with retry
        @self.retry_handler.with_async_retry
        async def _execute():
            return await self.async_client_wrapper.chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_prompt,
                **kwargs
            )
        
        raw_response = await _execute()
        
        # Process response
        text = ""
        if isinstance(raw_response, dict):
            # Extract text from Ollama response
            if "message" in raw_response:
                text = raw_response["message"].get("content", "")
            elif "response" in raw_response:
                text = raw_response["response"]
        
        # Extract token usage if available
        token_usage = None
        if isinstance(raw_response, dict):
            prompt_tokens = raw_response.get("prompt_eval_count", 0)
            completion_tokens = raw_response.get("eval_count", 0)
            if prompt_tokens or completion_tokens:
                token_usage = self.token_counter.extract_token_usage(
                    {
                        "prompt_eval_count": prompt_tokens,
                        "eval_count": completion_tokens,
                        "total_count": prompt_tokens + completion_tokens
                    },
                    self.model
                )
        
        response = LLMResponse(
            text=text,
            raw_response=raw_response,
            token_usage=token_usage
        )
        
        return response
    
    def stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolConfig]] = None,
        **kwargs
    ) -> Iterator[str]:
        """Stream synchronous chat completion."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        
        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)
        
        # Execute with retry
        @self.retry_handler.with_retry
        def _execute():
            return self.sync_client_wrapper.stream_chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_prompt,
                **kwargs
            )
        
        stream = _execute()
        
        # Process stream chunks
        for chunk in stream:
            if isinstance(chunk, dict):
                # Extract text from Ollama streaming response
                if "message" in chunk:
                    content = chunk["message"].get("content", "")
                    if content:
                        yield content
                elif "response" in chunk:
                    # Some Ollama versions use 'response' field
                    yield chunk["response"]
    
    async def async_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolConfig]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream asynchronous chat completion."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        
        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)
        
        # Execute with retry
        @self.retry_handler.with_async_retry
        async def _execute():
            return await self.async_client_wrapper.stream_chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system_prompt,
                **kwargs
            )
        
        stream = await _execute()
        
        # Process stream chunks
        async for chunk in stream:
            if isinstance(chunk, dict):
                # Extract text from Ollama streaming response
                if "message" in chunk:
                    content = chunk["message"].get("content", "")
                    if content:
                        yield content
                elif "response" in chunk:
                    yield chunk["response"]