"""Base adapter for phase-aware LLM operations."""

import logging
from typing import Any, Optional

from pydantic import BaseModel

from dipeo.diagram_generated import LLMRequestOptions

from ..drivers.base import BaseLLMAdapter
from .common import ExecutionPhase, MemorySelectionOutput

logger = logging.getLogger(__name__)


class PhaseAwareAdapter(BaseLLMAdapter):
    """Base adapter with execution phase support."""
    
    def prepare_request_with_phase(
        self, 
        messages: list[dict[str, str]], 
        **kwargs
    ) -> tuple[list[dict], dict, ExecutionPhase]:
        """
        Prepare request with phase awareness.
        
        Returns:
            Tuple of (processed_messages, api_params, execution_phase)
        """
        # Extract execution phase early
        execution_phase = kwargs.pop('execution_phase', ExecutionPhase.DEFAULT)
        if isinstance(execution_phase, str):
            try:
                execution_phase = ExecutionPhase(execution_phase)
            except ValueError:
                execution_phase = ExecutionPhase.DEFAULT
        
        # Handle LLMRequestOptions
        options = kwargs.get('options')
        if isinstance(options, LLMRequestOptions):
            if options.tools and self.supports_tools():
                kwargs['tools'] = options.tools
            if options.temperature is not None:
                kwargs['temperature'] = options.temperature
            if options.max_tokens is not None:
                kwargs['max_tokens'] = options.max_tokens
            if options.top_p is not None:
                kwargs['top_p'] = options.top_p
            if options.response_format is not None:
                kwargs['response_format'] = options.response_format
        
        # Process messages
        processed_messages = []
        system_prompt = None
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role in ["user", "assistant", "developer"]:
                processed_messages.append({"role": role, "content": content})
            else:
                logger.warning(f"Unknown role '{role}' in message, using 'user'")
                processed_messages.append({"role": "user", "content": content})
        
        # Extract API parameters
        api_params = {k: v for k, v in kwargs.items() if v is not None}
        
        # Handle memory selection phase with structured output
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            text_format = kwargs.get('text_format')
            if not text_format:  # Only set if not already provided
                api_params["_pydantic_model"] = MemorySelectionOutput
                logger.debug("Using structured output for memory selection phase")
        
        # Add back system prompt if exists
        if system_prompt:
            api_params["_system_prompt"] = system_prompt
        
        return processed_messages, api_params, execution_phase
    
    def should_use_structured_output(
        self, 
        execution_phase: ExecutionPhase,
        text_format: Optional[Any] = None
    ) -> Optional[type[BaseModel]]:
        """
        Determine if structured output should be used.
        
        Returns:
            Pydantic model class if structured output should be used, None otherwise
        """
        if text_format and isinstance(text_format, type) and issubclass(text_format, BaseModel):
            return text_format
        
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            return MemorySelectionOutput
        
        return None
    
    def extract_tools(self, kwargs: dict) -> list:
        """Extract and remove tools from kwargs."""
        return kwargs.pop('tools', [])