# openai_adapter.py

import base64
from typing import Any

from dipeo_domain import ChatResult, ToolOutput, ToolType, WebSearchResult, ImageGenerationResult
from openai import OpenAI

from ..base import BaseAdapter


class ChatGPTAdapter(BaseAdapter):
    """Compact adapter for OpenAI GPT models using Python SDK."""

    def _initialize_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def supports_tools(self) -> bool:
        supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1-nano']
        return any(model in self.model_name for model in supported_models)
    
    def supports_response_api(self) -> bool:
        return 'gpt-4o-mini' in self.model_name or 'gpt-4.1' in self.model_name

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        tools = kwargs.pop('tools', [])

        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Build input messages with response API format
        input_messages = []
        if system_prompt:
            # Response API uses developer instead of system
            input_messages.append({"role": "developer", "content": system_prompt})
        
        # Add other messages
        for msg in processed_messages:
            input_messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Convert tools to API format
        api_tools = []
        for tool in tools:
            if tool.type == "web_search_preview" or (hasattr(tool.type, 'value') and tool.type.value == "web_search_preview"):
                api_tools.append({"type": "web_search_preview"})
            elif tool.type == "image_generation" or (hasattr(tool.type, 'value') and tool.type.value == "image_generation"):
                api_tools.append({"type": "image_generation"})
        
        # Use base method to extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["temperature", "max_tokens"])
        
        # Make response API call
        try:
            response = self.client.responses.create(
                model=self.model_name,
                input=input_messages,
                tools=api_tools if api_tools else None,
                **api_params
            )
        except AttributeError:
            return ChatResult(text='', raw_response=None)
        
        # Extract text output
        text = getattr(response, 'output_text', '')
        
        # Process tool outputs
        tool_outputs = []
        if hasattr(response, 'output') and response.output:
            for output in response.output:
                if output.type == 'web_search_call' and hasattr(output, 'result'):
                    # Parse web search results
                    search_results = []
                    for result in output.result:
                        search_results.append(WebSearchResult(
                            url=result.get('url', ''),
                            title=result.get('title', ''),
                            snippet=result.get('snippet', ''),
                            score=result.get('score')
                        ))
                    tool_outputs.append(ToolOutput(
                        type=ToolType.WEB_SEARCH_PREVIEW,
                        result=search_results,
                        raw_response=output.result
                    ))
                elif output.type == 'image_generation_call' and hasattr(output, 'result'):
                    # Handle image generation result
                    tool_outputs.append(ToolOutput(
                        type=ToolType.IMAGE_GENERATION,
                        result=ImageGenerationResult(
                            image_data=output.result,  # Base64 encoded
                            format='png',
                            width=1024,  # Default values, could be extracted from metadata
                            height=1024
                        ),
                        raw_response=output.result
                    ))
        
        # Use base method to create token usage
        token_usage = self._create_token_usage(
            response,
            input_field="input_tokens",
            output_field="output_tokens"
        )
        
        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs if tool_outputs else None
        )

