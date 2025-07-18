"""Service for converting tool configurations."""

from typing import Any, List, Union

from dipeo.models import ToolConfig, ToolType


class ToolConfigurationService:
    """Service for converting tool configurations to proper format."""
    
    def convert_tools(self, tools: List[Union[str, dict, ToolConfig]]) -> List[ToolConfig]:
        """Convert various tool formats to ToolConfig instances.
        
        Args:
            tools: List of tools in string, dict, or ToolConfig format
            
        Returns:
            List of ToolConfig instances
        """
        tool_configs = []
        
        for tool in tools:
            if isinstance(tool, str):
                # Convert string to ToolConfig
                tool_config = self._convert_string_tool(tool)
                if tool_config:
                    tool_configs.append(tool_config)
            elif isinstance(tool, dict):
                # Already a dict, convert to ToolConfig
                tool_configs.append(ToolConfig(**tool))
            else:
                # Already a ToolConfig
                tool_configs.append(tool)
                
        return tool_configs
    
    def _convert_string_tool(self, tool: str) -> ToolConfig | None:
        """Convert string tool name to ToolConfig.
        
        Args:
            tool: Tool name as string
            
        Returns:
            ToolConfig instance or None if unknown tool
        """
        if tool in ['web_search', 'web_search_preview']:
            return ToolConfig(
                type=ToolType.web_search_preview,
                enabled=True
            )
        elif tool == 'image_generation':
            return ToolConfig(
                type=ToolType.image_generation,
                enabled=True
            )
        elif tool == 'voice':
            return ToolConfig(
                type=ToolType.voice,
                enabled=True
            )
        elif tool == 'speech_to_text':
            return ToolConfig(
                type=ToolType.speech_to_text,
                enabled=True
            )
        elif tool == 'text_to_speech':
            return ToolConfig(
                type=ToolType.text_to_speech,
                enabled=True
            )
        
        return None