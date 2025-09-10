"""Structured output capability for LLM providers."""

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError, create_model

from ..drivers.types import DecisionOutput, ExecutionPhase, MemorySelectionOutput, ProviderType

logger = logging.getLogger(__name__)


class StructuredOutputHandler:
    """Handles structured output for different providers."""

    def __init__(self, provider: ProviderType):
        """Initialize structured output handler for specific provider."""
        self.provider = provider

    def prepare_structured_output(
        self,
        response_format: type[BaseModel] | dict[str, Any] | None,
        execution_phase: ExecutionPhase = ExecutionPhase.DEFAULT,
    ) -> type[BaseModel] | dict[str, Any] | None:
        """Prepare structured output format for provider API.

        Returns:
        - For OpenAI: Pydantic model (for parse()) or None
        - For other providers: JSON schema dict or None
        """
        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            return self._prepare_memory_selection_format()

        if execution_phase == ExecutionPhase.DECISION_EVALUATION:
            return self._prepare_decision_evaluation_format()

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

    def _prepare_memory_selection_format(self) -> type[BaseModel] | dict[str, Any] | None:
        """Prepare format for memory selection phase."""
        if self.provider == ProviderType.OPENAI:
            # For OpenAI, return MemorySelectionOutput model directly
            return MemorySelectionOutput
        elif self.provider == ProviderType.ANTHROPIC:
            return {
                "type": "json",
                "json_schema": {
                    "type": "object",
                    "properties": {"message_ids": {"type": "array", "items": {"type": "string"}}},
                    "required": ["message_ids"],
                },
            }
        else:
            return {}

    def _prepare_decision_evaluation_format(self) -> type[BaseModel] | dict[str, Any] | None:
        """Prepare format for decision evaluation phase."""
        if self.provider == ProviderType.OPENAI:
            # For OpenAI, return DecisionOutput model directly
            return DecisionOutput
        elif self.provider == ProviderType.ANTHROPIC:
            return {
                "type": "json",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "decision": {
                            "type": "boolean",
                            "description": "The binary decision result",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Optional reasoning for the decision",
                        },
                    },
                    "required": ["decision"],
                },
            }
        else:
            return {}

    def _prepare_openai_format(
        self, response_format: type[BaseModel] | dict[str, Any]
    ) -> type[BaseModel] | None:
        """Prepare OpenAI structured output format.

        For OpenAI's new parse() API:
        - Pydantic models are returned as-is
        - JSON schemas are converted to Pydantic models
        - None for regular outputs
        """
        if isinstance(response_format, type) and issubclass(response_format, BaseModel):
            # Pydantic model - return as-is for parse()
            return response_format
        elif isinstance(response_format, dict):
            # JSON schema - convert to Pydantic model for parse()
            return self._json_schema_to_pydantic(response_format)
        else:
            # Unknown format - return None for regular output
            return None

    def _prepare_anthropic_format(
        self, response_format: type[BaseModel] | dict[str, Any]
    ) -> dict[str, Any]:
        """Prepare Anthropic/Claude structured output format."""
        if isinstance(response_format, type) and issubclass(response_format, BaseModel):
            # Pydantic model
            schema = response_format.model_json_schema()
            return {"type": "json", "json_schema": schema}
        elif isinstance(response_format, dict):
            # Raw JSON schema
            return {"type": "json", "json_schema": response_format}
        else:
            return {"type": "json"}

    def _prepare_google_format(
        self, response_format: type[BaseModel] | dict[str, Any]
    ) -> dict[str, Any]:
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
        response_format: type[BaseModel] | None = None,
        execution_phase: ExecutionPhase = ExecutionPhase.DEFAULT,
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

        # Handle decision evaluation phase
        if execution_phase == ExecutionPhase.DECISION_EVALUATION:
            try:
                return DecisionOutput(**parsed)
            except ValidationError as e:
                logger.error(f"Decision output validation failed: {e}")
                return parsed

        # Validate against Pydantic model if provided
        if (
            response_format
            and isinstance(response_format, type)
            and issubclass(response_format, BaseModel)
        ):
            try:
                return response_format(**parsed)
            except ValidationError as e:
                logger.error(f"Structured output validation failed: {e}")
                return parsed

        return parsed

    def format_structured_output(self, output: Any) -> str:
        """Format structured output for response."""
        if not output:
            return ""

        if isinstance(output, MemorySelectionOutput):
            # For memory selection, return just the message IDs as a JSON array
            return json.dumps(output.message_ids)
        elif isinstance(output, BaseModel):
            return json.dumps(output.model_dump())
        else:
            return json.dumps(output)

    def _json_schema_to_pydantic(self, schema: dict[str, Any]) -> type[BaseModel]:
        """Convert JSON schema to Pydantic model dynamically."""
        # Handle OpenAI's wrapped JSON schema format
        if "json_schema" in schema and isinstance(schema["json_schema"], dict):
            inner_schema = schema["json_schema"]
            actual_schema = inner_schema.get("schema", inner_schema)
            model_name = inner_schema.get("name", "DynamicModel")
        else:
            actual_schema = schema
            model_name = schema.get("name", "DynamicModel")

        # Build field definitions from schema properties
        field_definitions = {}
        properties = actual_schema.get("properties", {})
        required = actual_schema.get("required", [])

        for field_name, field_schema in properties.items():
            field_type = self._get_python_type(field_schema)
            if field_name in required:
                field_definitions[field_name] = (field_type, Field(...))
            else:
                field_definitions[field_name] = (Optional[field_type], Field(default=None))

        # Create the Pydantic model dynamically
        return create_model(model_name, **field_definitions)

    def _get_python_type(self, schema: dict[str, Any]) -> Any:
        """Convert JSON schema type to Python type."""
        json_type = schema.get("type", "string")

        if json_type == "string":
            return str
        elif json_type == "integer":
            return int
        elif json_type == "number":
            return float
        elif json_type == "boolean":
            return bool
        elif json_type == "array":
            item_type = self._get_python_type(schema.get("items", {}))
            return list[item_type]
        elif json_type == "object":
            # For nested objects, return Dict for simplicity
            return dict[str, Any]
        else:
            return Any
