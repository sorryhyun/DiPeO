"""Common components shared across LLM adapters."""

import json
import logging
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel

from dipeo.diagram_generated import (
    ImageGenerationResult,
    ToolOutput,
    ToolType,
    WebSearchResult,
)

logger = logging.getLogger(__name__)


class ExecutionPhase(str, Enum):
    """Execution phases for DiPeO workflows."""
    MEMORY_SELECTION = "memory_selection"
    DIRECT_EXECUTION = "direct_execution"
    DEFAULT = "default"


class MemorySelectionOutput(BaseModel):
    """Structured output model for memory selection phase."""
    message_ids: list[str]


def process_structured_output(parsed_output: Any) -> str:
    """Process structured output from LLM response."""
    if not parsed_output:
        return ''
    
    if isinstance(parsed_output, MemorySelectionOutput):
        # For memory selection, return just the message IDs as a JSON array
        return json.dumps(parsed_output.message_ids)
    elif isinstance(parsed_output, BaseModel):
        return json.dumps(parsed_output.model_dump())
    else:
        return json.dumps(parsed_output)


def convert_tools_to_api_format(tools: list, provider: str = "openai") -> list[dict]:
    """Convert tools to provider-specific API format."""
    api_tools = []
    
    if not tools:
        return api_tools
    
    for tool in tools:
        tool_type = tool.type if isinstance(tool.type, str) else tool.type.value
        
        if provider == "openai":
            if tool_type in ["web_search", "web_search_preview"]:
                api_tools.append({"type": "web_search_preview"})
            elif tool_type == "image_generation":
                api_tools.append({"type": "image_generation"})
        
        elif provider == "claude":
            if tool_type in ["web_search", "web_search_preview"]:
                api_tools.append({
                    "name": "web_search",
                    "description": "Search the web for information",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                })
            elif tool_type == "image_generation":
                api_tools.append({
                    "name": "generate_image",
                    "description": "Generate an image based on a text prompt",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The image generation prompt"
                            },
                            "size": {
                                "type": "string",
                                "description": "Image size",
                                "enum": ["1024x1024", "512x512", "256x256"],
                                "default": "1024x1024"
                            }
                        },
                        "required": ["prompt"]
                    }
                })
    
    return api_tools


def process_tool_outputs(response: Any, provider: str = "openai") -> list[ToolOutput] | None:
    """Process tool outputs from provider response."""
    tool_outputs = []
    
    if provider == "openai":
        if hasattr(response, 'output') and response.output:
            for output in response.output:
                if output.type == 'web_search_call' and hasattr(output, 'result'):
                    search_results = []
                    for result in output.result:
                        search_results.append(WebSearchResult(
                            url=result.get('url', ''),
                            title=result.get('title', ''),
                            snippet=result.get('snippet', ''),
                            score=result.get('score')
                        ))
                    tool_outputs.append(ToolOutput(
                        type=ToolType.WEB_SEARCH,
                        result=search_results,
                        raw_response=output.result
                    ))
                elif output.type == 'image_generation_call' and hasattr(output, 'result'):
                    tool_outputs.append(ToolOutput(
                        type=ToolType.IMAGE_GENERATION,
                        result=ImageGenerationResult(
                            image_data=output.result,  # Base64 encoded
                            format='png',
                            width=1024,
                            height=1024
                        ),
                        raw_response=output.result
                    ))
    
    return tool_outputs if tool_outputs else None


class MockResponse:
    """Mock response for error cases."""
    def __init__(self, text: str):
        self.output_text = text
        self.output = []
        self.usage = MockUsage()
        self.model = ""
        self.id = ""


class MockUsage:
    """Mock usage stats for error cases."""
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0


def create_empty_response(message: str) -> MockResponse:
    """Create an empty response object for error cases."""
    return MockResponse(message)