"""Base tool definition with Pydantic model support."""

from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from pydantic import BaseModel


@dataclass
class ToolDefinition:
    """Tool definition with Pydantic model for input validation and schema generation.

    Attributes:
        name: Tool name (e.g., "select_memory_messages")
        description: Human-readable description of what the tool does
        input_model: Pydantic BaseModel class for input validation
        handler: Async function that executes the tool
        group: Tool group for MCP organization (e.g., "memory", "decision")
        enabled: Whether the tool is enabled by default
        response_template: Optional template for formatting response text
    """

    name: str
    description: str
    input_model: type[BaseModel]
    handler: Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]
    group: str = "default"
    enabled: bool = True
    response_template: str = ""

    @property
    def input_schema(self) -> dict[str, Any]:
        """Generate JSON schema from Pydantic model."""
        schema = self.input_model.model_json_schema()
        # Remove metadata that MCP doesn't need
        schema.pop("title", None)
        return schema

    def to_sdk_tool_args(self) -> tuple[str, str, dict[str, Any]]:
        """Convert to arguments for claude_agent_sdk's @tool decorator.

        Returns:
            Tuple of (name, description, input_schema) for @tool decorator
        """
        return (self.name, self.description, self.input_schema)

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute the tool with validated input.

        Args:
            args: Raw input arguments (will be validated against input_model)

        Returns:
            Tool execution result
        """
        # Validate input using Pydantic model
        validated = self.input_model.model_validate(args)
        return await self.handler(validated.model_dump())
