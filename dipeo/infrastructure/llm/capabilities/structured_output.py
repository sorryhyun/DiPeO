"""Structured output capability for LLM providers."""

import json
import logging
from typing import Any, Dict, Optional, Type, Union

from pydantic import BaseModel, ValidationError

from ..core.types import ExecutionPhase, MemorySelectionOutput, ProviderType

logger = logging.getLogger(__name__)


class StructuredOutputHandler:
    """Handles structured output for different providers."""
    
    def __init__(self, provider: ProviderType):
        """Initialize structured output handler for specific provider."""
        self.provider = provider
    
    def prepare_structured_output(
        self,
        response_format: Optional[Union[Type[BaseModel], Dict[str, Any]]],
        execution_phase: ExecutionPhase = ExecutionPhase.DEFAULT
    ) -> Optional[Dict[str, Any]]:
        """Prepare structured output format for provider API."""
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            return self._prepare_memory_selection_format()
        
        if response_format is None:
            return None
        
        if self.provider == ProviderType.OPENAI:
            return self._prepare_openai_format(response_format)
        elif self.provider == ProviderType.ANTHROPIC:
            return self._prepare_anthropic_format(response_format)
        elif self.provider == ProviderType.GOOGLE:
            return self._prepare_google_format(response_format)
        else:
            return None
    
    def _prepare_memory_selection_format(self) -> Dict[str, Any]:
        """Prepare format for memory selection phase."""
        if self.provider == ProviderType.OPENAI:
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "memory_selection",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message_ids": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["message_ids"],
                        "additionalProperties": False
                    }
                }
            }
        elif self.provider == ProviderType.ANTHROPIC:
            return {
                "type": "json",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "message_ids": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["message_ids"]
                }
            }
        else:
            return {}
    
    def _prepare_openai_format(
        self,
        response_format: Union[Type[BaseModel], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare OpenAI structured output format."""
        if isinstance(response_format, type) and issubclass(response_format, BaseModel):
            # Pydantic model
            schema = response_format.model_json_schema()
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": response_format.__name__,
                    "strict": True,
                    "schema": schema
                }
            }
        elif isinstance(response_format, dict):
            # Raw JSON schema
            return {
                "type": "json_schema",
                "json_schema": response_format
            }
        else:
            return {"type": "json_object"}
    
    def _prepare_anthropic_format(
        self,
        response_format: Union[Type[BaseModel], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare Anthropic/Claude structured output format."""
        if isinstance(response_format, type) and issubclass(response_format, BaseModel):
            # Pydantic model
            schema = response_format.model_json_schema()
            return {
                "type": "json",
                "json_schema": schema
            }
        elif isinstance(response_format, dict):
            # Raw JSON schema
            return {
                "type": "json",
                "json_schema": response_format
            }
        else:
            return {"type": "json"}
    
    def _prepare_google_format(
        self,
        response_format: Union[Type[BaseModel], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare Google/Gemini structured output format."""
        if isinstance(response_format, type) and issubclass(response_format, BaseModel):
            # Pydantic model - Gemini uses response_schema
            schema = response_format.model_json_schema()
            return {"response_schema": schema}
        elif isinstance(response_format, dict):
            # Raw JSON schema
            return {"response_schema": response_format}
        else:
            return {}
    
    def process_structured_output(
        self,
        raw_output: str,
        response_format: Optional[Type[BaseModel]] = None,
        execution_phase: ExecutionPhase = ExecutionPhase.DEFAULT
    ) -> Any:
        """Process and validate structured output from response."""
        if not raw_output:
            return None
        
        # Parse JSON string if needed
        if isinstance(raw_output, str):
            try:
                parsed = json.loads(raw_output)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse structured output: {e}")
                return raw_output
        else:
            parsed = raw_output
        
        # Handle memory selection phase
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            try:
                return MemorySelectionOutput(**parsed)
            except ValidationError as e:
                logger.error(f"Memory selection output validation failed: {e}")
                return parsed
        
        # Validate against Pydantic model if provided
        if response_format and isinstance(response_format, type) and issubclass(response_format, BaseModel):
            try:
                return response_format(**parsed)
            except ValidationError as e:
                logger.error(f"Structured output validation failed: {e}")
                return parsed
        
        return parsed
    
    def format_structured_output(self, output: Any) -> str:
        """Format structured output for response."""
        if not output:
            return ''
        
        if isinstance(output, MemorySelectionOutput):
            # For memory selection, return just the message IDs as a JSON array
            return json.dumps(output.message_ids)
        elif isinstance(output, BaseModel):
            return json.dumps(output.model_dump())
        else:
            return json.dumps(output)