"""Structured output capability for LLM providers."""

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError, create_model

from dipeo.config.base_logger import get_module_logger

from ..drivers.types import DecisionOutput, ExecutionPhase, MemorySelectionOutput, ProviderType

logger = get_module_logger(__name__)


class StructuredOutputHandler:
    """Handles structured output for different providers."""

    def __init__(self, provider: ProviderType):
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
        if self.provider == ProviderType.OPENAI:
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
        if self.provider == ProviderType.OPENAI:
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
        """For OpenAI's parse() API: Pydantic models as-is, JSON schemas converted to Pydantic."""
        if isinstance(response_format, type) and issubclass(response_format, BaseModel):
            return response_format
        elif isinstance(response_format, dict):
            return self._json_schema_to_pydantic(response_format)
        else:
            return None

    def _prepare_anthropic_format(
        self, response_format: type[BaseModel] | dict[str, Any]
    ) -> dict[str, Any]:
        if isinstance(response_format, type) and issubclass(response_format, BaseModel):
            schema = response_format.model_json_schema()
            return {"type": "json", "json_schema": schema}
        elif isinstance(response_format, dict):
            return {"type": "json", "json_schema": response_format}
        else:
            return {"type": "json"}

    def _prepare_google_format(
        self, response_format: type[BaseModel] | dict[str, Any]
    ) -> dict[str, Any]:
        """Gemini uses response_schema format instead of json_schema."""
        if isinstance(response_format, type) and issubclass(response_format, BaseModel):
            schema = response_format.model_json_schema()
            return {"response_schema": schema}
        elif isinstance(response_format, dict):
            return {"response_schema": response_format}
        else:
            return {}

    def process_structured_output(
        self,
        raw_output: str,
        response_format: type[BaseModel] | None = None,
        execution_phase: ExecutionPhase = ExecutionPhase.DEFAULT,
    ) -> Any:
        if not raw_output:
            return None

        if isinstance(raw_output, str):
            try:
                parsed = json.loads(raw_output)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse structured output: {e}")
                return raw_output
        else:
            parsed = raw_output

        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            try:
                return MemorySelectionOutput(**parsed)
            except ValidationError as e:
                logger.error(f"Memory selection output validation failed: {e}")
                return parsed

        if execution_phase == ExecutionPhase.DECISION_EVALUATION:
            try:
                return DecisionOutput(**parsed)
            except ValidationError as e:
                logger.error(f"Decision output validation failed: {e}")
                return parsed

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
        if not output:
            return ""

        if isinstance(output, MemorySelectionOutput):
            # Return just message IDs as JSON array for memory selection
            return json.dumps(output.message_ids)
        elif isinstance(output, BaseModel):
            return json.dumps(output.model_dump())
        else:
            return json.dumps(output)

    def _json_schema_to_pydantic(self, schema: dict[str, Any]) -> type[BaseModel]:
        # Handle OpenAI's wrapped JSON schema format
        if "json_schema" in schema and isinstance(schema["json_schema"], dict):
            inner_schema = schema["json_schema"]
            actual_schema = inner_schema.get("schema", inner_schema)
            model_name = inner_schema.get("name", "DynamicModel")
        else:
            actual_schema = schema
            model_name = schema.get("name", "DynamicModel")

        field_definitions = {}
        properties = actual_schema.get("properties", {})
        required = actual_schema.get("required", [])

        for field_name, field_schema in properties.items():
            field_type = self._get_python_type(field_schema)
            if field_name in required:
                field_definitions[field_name] = (field_type, Field(...))
            else:
                field_definitions[field_name] = (Optional[field_type], Field(default=None))

        return create_model(model_name, **field_definitions)

    def _get_python_type(self, schema: dict[str, Any]) -> Any:
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
