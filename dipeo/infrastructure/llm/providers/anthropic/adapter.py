"""Anthropic adapter implementation."""

import logging
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from dipeo.config.llm import ANTHROPIC_DEFAULT_MAX_TOKENS
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
from .client import (
    AsyncAnthropicClientWrapper,
    AnthropicClientWrapper,
)

logger = logging.getLogger(__name__)


class AnthropicAdapter(UnifiedAdapter):
    """Unified Anthropic/Claude adapter with all capabilities."""
    
    def __init__(self, config: AdapterConfig):
        """Initialize Anthropic adapter with capabilities."""
        # Initialize clients first (needed by parent __init__)
        self.sync_client_wrapper = AnthropicClientWrapper(config)
        self.async_client_wrapper = AsyncAnthropicClientWrapper(config)
        
        # Now call parent __init__ which will use _create_sync_client and _create_async_client
        super().__init__(config)
        
        # Initialize capabilities
        self.tool_handler = ToolHandler(ProviderType.ANTHROPIC)
        self.structured_output_handler = StructuredOutputHandler(ProviderType.ANTHROPIC)
        self.streaming_handler = StreamingHandler(
            ProviderType.ANTHROPIC,
            StreamConfig(mode=config.streaming_mode)
        )
        self.retry_handler = RetryHandler(
            ProviderType.ANTHROPIC,
            RetryConfig(
                max_attempts=config.max_retries,
                initial_delay=config.retry_delay,
                backoff_factor=config.retry_backoff
            )
        )
        self.phase_handler = PhaseHandler(ProviderType.ANTHROPIC)
        
        # Initialize processors
        self.message_processor = MessageProcessor(ProviderType.ANTHROPIC)
        self.response_processor = ResponseProcessor(ProviderType.ANTHROPIC)
        self.token_counter = TokenCounter(ProviderType.ANTHROPIC)
    
    def _get_capabilities(self) -> ProviderCapabilities:
        """Get Anthropic provider capabilities."""
        return ProviderCapabilities(
            supports_async=True,
            supports_streaming=True,
            supports_tools=True,
            supports_structured_output=True,
            supports_vision=True,
            supports_web_search=False,  # Not native, but can be added via tools
            supports_image_generation=False,
            supports_computer_use=False,  # Computer use is only for Claude Code
            max_context_length=200000,  # Claude 3.5 default
            max_output_tokens=8192,
            supported_models={
                "claude-3-5-sonnet-latest",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-latest",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-latest",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1",
                "claude-2.0",
                "claude-instant-1.2",
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
        return model in self.capabilities.supported_models or model.startswith("claude-")
    
    def prepare_messages(self, messages: List[Message]) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Prepare messages for Anthropic API, extracting system prompt."""
        # Apply phase-specific preparation
        if self.config.execution_phase != ExecutionPhase.DEFAULT:
            messages = self.phase_handler.prepare_messages_for_phase(
                messages, self.config.execution_phase
            )
        
        # Extract system prompt (Anthropic handles it separately)
        system_prompt = self.message_processor.extract_system_prompt(messages)
        
        # Filter out system messages and process the rest
        non_system_messages = [msg for msg in messages if msg.role != "system"]
        prepared_messages = self.message_processor.prepare_messages(non_system_messages)
        
        return prepared_messages, system_prompt
    
    def _prepare_tools(self, tools: List[ToolConfig]) -> List[Dict[str, Any]]:
        """Prepare tools for Anthropic API."""
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
        max_tokens = max_tokens or self.config.max_tokens or ANTHROPIC_DEFAULT_MAX_TOKENS  # Anthropic requires max_tokens
        execution_phase = execution_phase or self.config.execution_phase
        
        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)
        
        # Validate token limit
        if not self.token_counter.validate_token_limit(
            prepared_messages, self.model, max_tokens
        ):
            raise ValueError("Messages exceed model's context limit")
        
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
            "system": system_prompt,
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
            # For Anthropic, structured output comes from tool use
            if hasattr(raw_response, 'content') and isinstance(raw_response.content, list):
                for block in raw_response.content:
                    if block.type == 'tool_use' and block.name == 'respond_with_structure':
                        response.structured_output = self.structured_output_handler.process_structured_output(
                            block.input, response_format, execution_phase
                        )
                        break
        
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
        max_tokens = max_tokens or self.config.max_tokens or ANTHROPIC_DEFAULT_MAX_TOKENS
        execution_phase = execution_phase or self.config.execution_phase
        
        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)
        
        # Validate token limit
        if not self.token_counter.validate_token_limit(
            prepared_messages, self.model, max_tokens
        ):
            raise ValueError("Messages exceed model's context limit")
        
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
            "system": system_prompt,
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
            # For Anthropic, structured output comes from tool use
            if hasattr(raw_response, 'content') and isinstance(raw_response.content, list):
                for block in raw_response.content:
                    if block.type == 'tool_use' and block.name == 'respond_with_structure':
                        response.structured_output = self.structured_output_handler.process_structured_output(
                            block.input, response_format, execution_phase
                        )
                        break
        
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
        max_tokens = max_tokens or self.config.max_tokens or ANTHROPIC_DEFAULT_MAX_TOKENS
        
        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)
        
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
                system=system_prompt,
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
        max_tokens = max_tokens or self.config.max_tokens or ANTHROPIC_DEFAULT_MAX_TOKENS
        
        # Prepare messages and extract system prompt
        prepared_messages, system_prompt = self.prepare_messages(messages)
        
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
                system=system_prompt,
                **kwargs
            )
        
        stream = await _execute()
        
        # Wrap with streaming handler
        async for chunk in self.streaming_handler.create_async_stream_wrapper(stream):
            yield chunk