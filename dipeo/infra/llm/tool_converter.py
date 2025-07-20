from typing import List, Dict, Any, Union, Optional, Protocol
from enum import Enum
import logging

from dipeo.models import ToolConfig, ToolType

logger = logging.getLogger(__name__)


class ProviderToolFormat(Protocol):
    """Protocol for provider-specific tool format"""
    pass


class ToolConverter:
    """Centralized tool conversion utility for LLM providers"""
    
    @staticmethod
    def normalize_tools(
        tools: Optional[Union[List[str], List[Dict[str, Any]], List[ToolConfig]]]
    ) -> List[ToolConfig]:
        """
        Convert various tool input formats to standardized ToolConfig list.
        
        Supports:
        - List of strings: ['web_search', 'image_generation']
        - List of dicts: [{'type': 'web_search', 'enabled': True}]
        - List of ToolConfig objects
        """
        if not tools:
            return []
        
        normalized = []
        
        for tool in tools:
            if isinstance(tool, str):
                # Convert string to ToolConfig
                tool_config = ToolConverter._string_to_tool_config(tool)
                if tool_config:
                    normalized.append(tool_config)
            elif isinstance(tool, dict):
                # Convert dict to ToolConfig
                try:
                    normalized.append(ToolConfig(**tool))
                except Exception as e:
                    logger.warning(f"Failed to convert tool dict {tool}: {e}")
            elif isinstance(tool, ToolConfig):
                # Already a ToolConfig
                normalized.append(tool)
            else:
                logger.warning(f"Unknown tool format: {type(tool)}")
        
        return normalized
    
    @staticmethod
    def _string_to_tool_config(tool_string: str) -> Optional[ToolConfig]:
        """Convert tool string to ToolConfig"""
        # Map common string variations to ToolType
        tool_map = {
            'web_search': ToolType.web_search,
            'web_search_preview': ToolType.web_search_preview,
            'image_generation': ToolType.image_generation,
            'voice': ToolType.voice,
            'speech_to_text': ToolType.speech_to_text,
            'text_to_speech': ToolType.text_to_speech,
        }
        
        tool_type = tool_map.get(tool_string.lower())
        if tool_type:
            return ToolConfig(type=tool_type, enabled=True)
        
        logger.warning(f"Unknown tool string: {tool_string}")
        return None
    
    @staticmethod
    def to_openai_format(tools: List[ToolConfig]) -> List[Dict[str, Any]]:
        """Convert ToolConfig list to OpenAI function format"""
        openai_tools = []
        
        for tool in tools:
            if not tool.enabled:
                continue
                
            if tool.type == ToolType.web_search_preview:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web for information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                })
            elif tool.type == ToolType.image_generation:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": "generate_image",
                        "description": "Generate an image from a text description",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The image description"
                                },
                                "size": {
                                    "type": "string",
                                    "enum": ["1024x1024", "1792x1024", "1024x1792"],
                                    "default": "1024x1024"
                                }
                            },
                            "required": ["prompt"]
                        }
                    }
                })
        
        return openai_tools
    
    @staticmethod
    def to_claude_format(tools: List[ToolConfig]) -> List[Dict[str, Any]]:
        """Convert ToolConfig list to Claude tool format"""
        claude_tools = []
        
        for tool in tools:
            if not tool.enabled:
                continue
                
            if tool.type == ToolType.web_search_preview:
                claude_tools.append({
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
            elif tool.type == ToolType.image_generation:
                claude_tools.append({
                    "name": "generate_image",
                    "description": "Generate an image from a text description",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The image description"
                            }
                        },
                        "required": ["prompt"]
                    }
                })
        
        return claude_tools
    
    @staticmethod
    def to_gemini_format(tools: List[ToolConfig]) -> List[Dict[str, Any]]:
        """Convert ToolConfig list to Gemini tool format"""
        gemini_tools = []
        
        for tool in tools:
            if not tool.enabled:
                continue
                
            if tool.type == ToolType.web_search_preview:
                gemini_tools.append({
                    "name": "search",
                    "description": "Search the web for information"
                })
            elif tool.type == ToolType.image_generation:
                # Gemini may handle image generation differently
                logger.info("Image generation tool requested for Gemini")
        
        return gemini_tools
    
    @staticmethod
    def extract_tool_types(tools: List[ToolConfig]) -> List[ToolType]:
        """Extract enabled tool types from ToolConfig list"""
        return [tool.type for tool in tools if tool.enabled]
    
    @staticmethod
    def has_tool_type(tools: List[ToolConfig], tool_type: ToolType) -> bool:
        """Check if a specific tool type is enabled in the list"""
        return any(tool.type == tool_type and tool.enabled for tool in tools)