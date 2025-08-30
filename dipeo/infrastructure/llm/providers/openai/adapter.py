"""OpenAI adapter implementation."""

import logging
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union

from dipeo.diagram_generated import Message, ToolConfig

from ...capabilities import (
    PhaseHandler,
    RetryHandler,
    StreamingHandler,
    StructuredOutputHandler,
    ToolHandler,
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
from .client import AsyncOpenAIClientWrapper, OpenAIClientWrapper

logger = logging.getLogger(__name__)


class OpenAIAdapter(UnifiedAdapter):
    """Unified OpenAI adapter with all capabilities."""
    
    def __init__(self, config: AdapterConfig):
        """Initialize OpenAI adapter with capabilities."""
        # Initialize clients first (before calling super().__init__)
        self.sync_client_wrapper = OpenAIClientWrapper(config)
        self.async_client_wrapper = AsyncOpenAIClientWrapper(config)
        
        # Now call parent init
        super().__init__(config)
        
        # Initialize capabilities
        self.tool_handler = ToolHandler(ProviderType.OPENAI)
        self.structured_output_handler = StructuredOutputHandler(ProviderType.OPENAI)
        self.streaming_handler = StreamingHandler(
            ProviderType.OPENAI,
            StreamConfig(mode=config.streaming_mode)
        )
        self.retry_handler = RetryHandler(
            ProviderType.OPENAI,
            RetryConfig(
                max_attempts=config.max_retries,
                initial_delay=config.retry_delay,
                backoff_factor=config.retry_backoff
            )
        )
        self.phase_handler = PhaseHandler(ProviderType.OPENAI)
        
        # Initialize processors
        self.message_processor = MessageProcessor(ProviderType.OPENAI)
        self.response_processor = ResponseProcessor(ProviderType.OPENAI)
        self.token_counter = TokenCounter(ProviderType.OPENAI)
    
    def _get_capabilities(self) -> ProviderCapabilities:
        """Get OpenAI provider capabilities."""
        return ProviderCapabilities(
            supports_async=True,
            supports_streaming=True,
            supports_tools=True,
            supports_structured_output=True,
            supports_vision=True,
            supports_web_search=True,
            supports_image_generation=True,
            supports_computer_use=False,
            max_context_length=128000,  # GPT-4o default
            max_output_tokens=4096,
            supported_models={
                "gpt-5-nano-2025-08-07",
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
                "o3",
                "o3-mini",
            },
            streaming_modes={StreamingMode.NONE, StreamingMode.SSE}
        )
    
    def _create_sync_client(self):
        """Create synchronous client."""
        return self.sync_client_wrapper
    
    async def _create_async_client(self):
        """Create asynchronous client."""
        return self.async_client_wrapper
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is supported."""
        return model in self.capabilities.supported_models or model.startswith("gpt-")
    
    def prepare_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Prepare messages for OpenAI API."""
        # Apply phase-specific preparation
        if self.config.execution_phase != ExecutionPhase.DEFAULT:
            messages = self.phase_handler.prepare_messages_for_phase(
                messages, self.config.execution_phase
            )
        
        # Process messages
        return self.message_processor.prepare_messages(messages)
    
    def _prepare_tools(self, tools: List[ToolConfig]) -> List[Dict[str, Any]]:
        """Prepare tools for OpenAI API."""
        return self.tool_handler.convert_tools_to_api_format(tools)
    
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
        execution_phase = execution_phase or self.config.execution_phase
        
        # Prepare messages
        prepared_messages = self.prepare_messages(messages)
        
        # Skip local token validation - let the API handle context limits
        # The API will reject oversized requests and provide accurate token counts
        # Local estimation without tiktoken is inaccurate and causes false positives
        
        # Prepare tools
        api_tools = self._prepare_tools(tools) if tools else None
        
        # Prepare structured output
        api_response_format = None
        if execution_phase == ExecutionPhase.MEMORY_SELECTION or response_format:
            api_response_format = self.structured_output_handler.prepare_structured_output(
                response_format, execution_phase
            )
        
        # Get phase-specific parameters
        phase_params = self.phase_handler.get_phase_specific_params(execution_phase)
        
        # Merge parameters
        final_params = {
            **kwargs,
            **phase_params,
            "temperature": phase_params.get("temperature", temperature),
            "max_tokens": phase_params.get("max_tokens", max_tokens),
        }
        
        # Execute with retry
        @self.retry_handler.with_retry
        def _execute():
            return self.sync_client_wrapper.chat_completion(
                messages=prepared_messages,
                model=self.model,
                tools=api_tools,
                response_format=api_response_format,
                **final_params
            )
        
        raw_response = _execute()
        
        # Process response
        response = self.response_processor.process_response(raw_response, self.model)
        
        # Process phase-specific response
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            response.structured_output = self.phase_handler.process_phase_response(
                raw_response, execution_phase
            )
        elif response_format:
            response.structured_output = self.structured_output_handler.process_structured_output(
                response.content, response_format, execution_phase
            )
        
        # Process tool outputs
        if tools:
            response.tool_outputs = self.tool_handler.process_tool_outputs(raw_response)
        
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
        execution_phase = execution_phase or self.config.execution_phase
        
        # Prepare messages
        prepared_messages = self.prepare_messages(messages)
        
        # Skip local token validation - let the API handle context limits
        # The API will reject oversized requests and provide accurate token counts
        # Local estimation without tiktoken is inaccurate and causes false positives
        
        # Prepare tools
        api_tools = self._prepare_tools(tools) if tools else None
        
        # Prepare structured output
        api_response_format = None
        if execution_phase == ExecutionPhase.MEMORY_SELECTION or response_format:
            api_response_format = self.structured_output_handler.prepare_structured_output(
                response_format, execution_phase
            )
        
        # Get phase-specific parameters
        phase_params = self.phase_handler.get_phase_specific_params(execution_phase)
        
        # Merge parameters (exclude response_format from both kwargs and phase_params to avoid duplication)
        kwargs_without_response_format = {k: v for k, v in kwargs.items() if k != 'response_format'}
        phase_params_without_response_format = {k: v for k, v in phase_params.items() if k != 'response_format'}
        final_params = {
            **kwargs_without_response_format,
            **phase_params_without_response_format,
            "temperature": phase_params.get("temperature", temperature),
            "max_tokens": phase_params.get("max_tokens", max_tokens),
        }
        
        # Execute with retry
        @self.retry_handler.with_async_retry
        async def _execute():
            return await self.async_client_wrapper.chat_completion(
                messages=prepared_messages,
                model=self.model,
                tools=api_tools,
                response_format=api_response_format,
                **final_params
            )
        
        raw_response = await _execute()
        
        # Process response
        response = self.response_processor.process_response(raw_response, self.model)
        
        # Process phase-specific response
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            response.structured_output = self.phase_handler.process_phase_response(
                raw_response, execution_phase
            )
        elif response_format:
            response.structured_output = self.structured_output_handler.process_structured_output(
                response.content, response_format, execution_phase
            )
        
        # Process tool outputs
        if tools:
            response.tool_outputs = self.tool_handler.process_tool_outputs(raw_response)
        
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
        
        # Prepare messages
        prepared_messages = self.prepare_messages(messages)
        
        # Prepare tools
        api_tools = self._prepare_tools(tools) if tools else None
        
        # Execute with retry
        @self.retry_handler.with_retry
        def _execute():
            return self.sync_client_wrapper.stream_chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=api_tools,
                **kwargs
            )
        
        stream = _execute()
        
        # Wrap with streaming handler
        for chunk in self.streaming_handler.create_sync_stream_wrapper(stream):
            yield chunk
    
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
        
        # Prepare messages
        prepared_messages = self.prepare_messages(messages)
        
        # Prepare tools
        api_tools = self._prepare_tools(tools) if tools else None
        
        # Execute with retry
        @self.retry_handler.with_async_retry
        async def _execute():
            return await self.async_client_wrapper.stream_chat_completion(
                messages=prepared_messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=api_tools,
                **kwargs
            )
        
        stream = await _execute()
        
        # Wrap with streaming handler
        async for chunk in self.streaming_handler.create_async_stream_wrapper(stream):
            yield chunk