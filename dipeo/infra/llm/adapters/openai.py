# openai_adapter.py

import logging

from openai import OpenAI

from dipeo.models import ChatResult, ImageGenerationResult, ToolOutput, ToolType, WebSearchResult

from ..base import BaseLLMAdapter

logger = logging.getLogger(__name__)


class ChatGPTAdapter(BaseLLMAdapter):
    """Compact adapter for OpenAI GPT models using Python SDK."""

    def _initialize_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def supports_tools(self) -> bool:
        # Models that support tools including websearch via responses API
        supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini']
        return any(model in self.model_name for model in supported_models)
    
    def supports_response_api(self) -> bool:
        return 'gpt-4o-mini' in self.model_name or 'gpt-4.1' in self.model_name

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        tools = kwargs.pop('tools', [])
        system_prompt_kwarg = kwargs.pop('system_prompt', None)

        # Guard against None or empty messages
        if not messages:
            logger.warning("No messages provided to OpenAI API call")
            return ChatResult(text='', raw_response=None)

        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Use system_prompt from kwargs if provided, otherwise use extracted one
        if system_prompt_kwarg:
            system_prompt = system_prompt_kwarg
        
        # Build input messages with response API format
        input_messages = []
        if system_prompt:
            # Response API uses developer instead of system
            input_messages.append({"role": "developer", "content": system_prompt})
        
        # Add other messages
        for msg in processed_messages:
            input_messages.append({"role": msg["role"], "content": msg["content"]})

        print(f"[OPENAI DEBUG] Input text: {input_messages}")
        # Convert tools to API format
        api_tools = []
        if tools:
            for tool in tools:
                if tool.type == "web_search_preview" or (hasattr(tool.type, 'value') and tool.type.value == "web_search_preview"):
                    api_tools.append({"type": "web_search_preview"})
                elif tool.type == "image_generation" or (hasattr(tool.type, 'value') and tool.type.value == "image_generation"):
                    api_tools.append({"type": "image_generation"})
        
        # Only log tools in debug mode if needed
        # if api_tools:
        #     logger.debug(f"API tools: {api_tools}")
        
        # Use base method to extract allowed parameters
        # Note: responses API doesn't support max_tokens parameter
        api_params = self._extract_api_params(kwargs, ["temperature"])
        
        # Make response API call
        try:
            # Build API call parameters
            create_params = {
                "model": self.model_name,
                "input": input_messages,
                **api_params
            }
            
            # Add tools if they exist and are supported
            if api_tools and self.supports_tools():
                create_params["tools"] = api_tools
                logger.debug(f"Using tools with responses API: {api_tools}")

            response = self.client.responses.create(**create_params)
        except Exception as e:
            logger.error(f"Error calling OpenAI responses API: {type(e).__name__}: {e!s}")
            return ChatResult(text='', raw_response=None)
        
        # Extract text output
        text = getattr(response, 'output_text', '')
        print(f"[OPENAI DEBUG] Output text: {text}")
        
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
                        type=ToolType.web_search,
                        result=search_results,
                        raw_response=output.result
                    ))
                elif output.type == 'image_generation_call' and hasattr(output, 'result'):
                    # Handle image generation result
                    tool_outputs.append(ToolOutput(
                        type=ToolType.image_generation,
                        result=ImageGenerationResult(
                            image_data=output.result,  # Base64 encoded
                            format='png',
                            width=1024,  # Default values, could be extracted from metadata
                            height=1024
                        ),
                        raw_response=output.result
                    ))
        
        # Create token usage without logging
        token_usage = self._create_token_usage(
            response,
            input_field="input_tokens",
            output_field="output_tokens"
        )
        
        result = ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs if tool_outputs else None
        )
        
        return result
