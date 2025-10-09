"""Tool handling capability for LLM providers."""

import logging
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import (
    ImageGenerationResult,
    ToolConfig,
    ToolOutput,
    ToolType,
    WebSearchResult,
)

from ..drivers.types import ProviderType

logger = get_module_logger(__name__)


class ToolHandler:
    """Handles tool conversion and processing for different providers."""

    def __init__(self, provider: ProviderType):
        """Initialize tool handler for specific provider."""
        self.provider = provider

    def convert_tools_to_api_format(self, tools: list[ToolConfig]) -> list[dict[str, Any]]:
        """Convert tools to provider-specific API format."""
        if not tools:
            return []

        if self.provider == ProviderType.OPENAI:
            return self._convert_tools_openai(tools)
        elif self.provider == ProviderType.ANTHROPIC:
            return self._convert_tools_anthropic(tools)
        elif self.provider == ProviderType.GOOGLE:
            return self._convert_tools_google(tools)
        else:
            return []

    def _convert_tools_openai(self, tools: list[ToolConfig]) -> list[dict[str, Any]]:
        """Convert tools to OpenAI format."""
        api_tools = []

        for tool in tools:
            tool_type = tool.type if isinstance(tool.type, str) else tool.type.value

            if tool_type in ["web_search", "web_search_preview"]:
                api_tools.append({"type": "web_search_preview"})
            elif tool_type == "image_generation":
                api_tools.append({"type": "image_generation"})
            elif tool_type == "function":
                # Function calling format for OpenAI
                api_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters if hasattr(tool, "parameters") else {},
                        },
                    }
                )

        return api_tools

    def _convert_tools_anthropic(self, tools: list[ToolConfig]) -> list[dict[str, Any]]:
        """Convert tools to Anthropic/Claude format."""
        api_tools = []

        for tool in tools:
            tool_type = tool.type if isinstance(tool.type, str) else tool.type.value

            if tool_type in ["web_search", "web_search_preview"]:
                api_tools.append(
                    {
                        "name": "web_search",
                        "description": "Search the web for information",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search query"}
                            },
                            "required": ["query"],
                        },
                    }
                )
            elif tool_type == "image_generation":
                api_tools.append(
                    {
                        "name": "generate_image",
                        "description": "Generate an image based on a text prompt",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The image generation prompt",
                                },
                                "size": {
                                    "type": "string",
                                    "description": "Image size",
                                    "enum": ["1024x1024", "512x512", "256x256"],
                                    "default": "1024x1024",
                                },
                            },
                            "required": ["prompt"],
                        },
                    }
                )
            elif tool_type == "function":
                # Function calling format for Anthropic
                api_tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.parameters
                        if hasattr(tool, "parameters")
                        else {"type": "object", "properties": {}, "required": []},
                    }
                )
            elif tool_type == "computer_use":
                # Computer use tools for Claude
                api_tools.append(
                    {
                        "name": "computer",
                        "type": "computer_20241022",
                        "display_width_px": 1920,
                        "display_height_px": 1080,
                        "display_number": 0,
                    }
                )

        return api_tools

    def _convert_tools_google(self, tools: list[ToolConfig]) -> list[dict[str, Any]]:
        """Convert tools to Google/Gemini format."""
        api_tools = []

        for tool in tools:
            tool_type = tool.type if isinstance(tool.type, str) else tool.type.value

            if tool_type == "function":
                # Function calling format for Gemini
                api_tools.append(
                    {
                        "function_declarations": [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.parameters
                                if hasattr(tool, "parameters")
                                else {},
                            }
                        ]
                    }
                )

        return api_tools

    def process_tool_outputs(self, response: Any) -> list[ToolOutput] | None:
        """Process tool outputs from provider response."""
        if self.provider == ProviderType.OPENAI:
            return self._process_openai_tool_outputs(response)
        elif self.provider == ProviderType.ANTHROPIC:
            return self._process_anthropic_tool_outputs(response)
        elif self.provider == ProviderType.GOOGLE:
            return self._process_google_tool_outputs(response)
        else:
            return None

    def _process_openai_tool_outputs(self, response: Any) -> list[ToolOutput] | None:
        """Process OpenAI tool outputs."""
        tool_outputs = []

        if hasattr(response, "output") and response.output:
            for output in response.output:
                if output.type == "web_search_call" and hasattr(output, "result"):
                    search_results = []
                    for result in output.result:
                        search_results.append(
                            WebSearchResult(
                                url=result.get("url", ""),
                                title=result.get("title", ""),
                                snippet=result.get("snippet", ""),
                                score=result.get("score"),
                            )
                        )
                    tool_outputs.append(
                        ToolOutput(
                            type=ToolType.WEB_SEARCH,
                            result=search_results,
                            raw_response=output.result,
                        )
                    )
                elif output.type == "image_generation_call" and hasattr(output, "result"):
                    tool_outputs.append(
                        ToolOutput(
                            type=ToolType.IMAGE_GENERATION,
                            result=ImageGenerationResult(
                                image_data=output.result,  # Base64 encoded
                                format="png",
                                width=1024,
                                height=1024,
                            ),
                            raw_response=output.result,
                        )
                    )
                elif output.type == "function_call" and hasattr(output, "result"):
                    tool_outputs.append(
                        ToolOutput(
                            type=ToolType.FUNCTION, result=output.result, raw_response=output.result
                        )
                    )

        return tool_outputs if tool_outputs else None

    def _process_anthropic_tool_outputs(self, response: Any) -> list[ToolOutput] | None:
        """Process Anthropic/Claude tool outputs."""
        tool_outputs = []

        if hasattr(response, "content") and isinstance(response.content, list):
            for content_block in response.content:
                if content_block.type == "tool_use":
                    if content_block.name == "web_search":
                        # Process web search results
                        tool_outputs.append(
                            ToolOutput(
                                type=ToolType.WEB_SEARCH,
                                result=content_block.input,
                                raw_response=content_block,
                            )
                        )
                    elif content_block.name == "generate_image":
                        # Process image generation
                        tool_outputs.append(
                            ToolOutput(
                                type=ToolType.IMAGE_GENERATION,
                                result=content_block.input,
                                raw_response=content_block,
                            )
                        )
                    else:
                        # Generic function call
                        tool_outputs.append(
                            ToolOutput(
                                type=ToolType.FUNCTION,
                                result=content_block.input,
                                raw_response=content_block,
                            )
                        )

        return tool_outputs if tool_outputs else None

    def _process_google_tool_outputs(self, response: Any) -> list[ToolOutput] | None:
        """Process Google/Gemini tool outputs."""
        tool_outputs = []

        if hasattr(response, "candidates") and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call"):
                            tool_outputs.append(
                                ToolOutput(
                                    type=ToolType.FUNCTION,
                                    result={
                                        "name": part.function_call.name,
                                        "args": part.function_call.args,
                                    },
                                    raw_response=part.function_call,
                                )
                            )

        return tool_outputs if tool_outputs else None
