import asyncio
import base64
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from google import genai
from google.genai import types

from dipeo.models import (
    ChatResult,
    ImageGenerationResult,
    LLMRequestOptions,
    ToolOutput,
    ToolType,
    WebSearchResult,
)

from ...services.llm.base import BaseLLMAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseLLMAdapter):
    """Adapter for Google Gemini models via the genai API."""

    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name, api_key, base_url)
        self.max_retries = 3
        self.retry_delay = 1.0

    def _initialize_client(self) -> Any:
        return genai.Client(api_key=self.api_key)
    
    def supports_tools(self) -> bool:
        supported_models = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.0-flash', 
                           'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite']
        return any(model in self.model_name for model in supported_models)

    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make API call to Gemini and return ChatResult."""
        # Check if we should handle tools
        tools = kwargs.pop('tools', None)
        
        # Handle special cases: image generation
        if tools and any(tool.type == ToolType.IMAGE_GENERATION or 
                        (hasattr(tool.type, 'value') and tool.type.value == "image_generation") 
                        for tool in tools):
            return self._make_image_generation_call(messages, **kwargs)
        
        # Use base method to extract system prompt and messages
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in processed_messages:
            role = msg["role"]
            content = msg["content"]
            
            # Convert role names and content format
            parts = self._convert_content_to_parts(content)
            if role == "assistant":
                gemini_messages.append({"role": "model", "parts": parts})
            else:  # user role
                gemini_messages.append({"role": "user", "parts": parts})

        # Convert tools to Gemini function declarations if provided
        gemini_tools = None
        if tools and self.supports_tools():
            gemini_tools = self._convert_tools_to_gemini_format(tools)
        
        # Get the model with system instruction
        # Note: tools parameter should be in generation config, not model init
        model = self.client.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
        )

        # Use base method to extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["max_tokens", "temperature"])

        # Create generation config with tools if provided
        config_params = {
            "max_output_tokens": api_params.get("max_tokens"),
            "temperature": api_params.get("temperature"),
        }
        if gemini_tools:
            config_params["tools"] = gemini_tools
            # Set function calling mode
            config_params["tool_config"] = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="AUTO"  # Let the model decide when to use tools
                )
            )
        generation_config = self.client.GenerationConfig(**config_params)

        # Make the API call with retry logic
        response = self._make_api_call_with_retry(
            model=model,
            contents=gemini_messages,
            generation_config=generation_config,
            safety_settings=kwargs.get("gemini_safety_settings"),
        )

        # Process response and handle function calls
        text = ""
        tool_outputs = []
        
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text += part.text
                    elif hasattr(part, 'function_call') and part.function_call:
                        # Handle function calls
                        func_call = part.function_call
                        tool_output = self._process_function_call(func_call)
                        if tool_output:
                            tool_outputs.append(tool_output)

        # Use base method to create token usage
        # Note: Gemini response structure may vary, so we handle it carefully
        token_usage = None
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            if hasattr(usage, 'prompt_token_count') and hasattr(usage, 'candidates_token_count'):
                token_usage = self._create_token_usage(
                    response,
                    input_field="prompt_token_count",
                    output_field="candidates_token_count",
                    usage_attr="usage_metadata"
                )

        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs if tool_outputs else None,
        )
    
    def _convert_tools_to_gemini_format(self, tools: list) -> list[types.Tool]:
        function_declarations = []
        
        for tool in tools:
            tool_type = tool.type if isinstance(tool.type, str) else tool.type.value
            
            if tool_type == "web_search" or tool_type == "web_search_preview":
                # Define web search function following official format
                function_declarations.append(types.FunctionDeclaration(
                    name="web_search",
                    description="Search the web for information",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                ))
            elif tool_type == "image_generation":
                # Define image generation function
                function_declarations.append(types.FunctionDeclaration(
                    name="generate_image",
                    description="Generate an image based on a text prompt",
                    parameters={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The image generation prompt"
                            },
                            "size": {
                                "type": "string",
                                "description": "Image size",
                                "enum": ["1024x1024", "512x512", "256x256"]
                            }
                        },
                        "required": ["prompt"]
                    }
                ))
            # Add more tool types as needed
        
        if function_declarations:
            return [types.Tool(function_declarations=function_declarations)]
        return None
    
    def _process_function_call(self, function_call) -> ToolOutput | None:
        """Process a function call from Gemini response."""
        if function_call.name == "web_search":
            query = function_call.args.get("query", "")
            # Note: This returns placeholder data. In production, you would
            # execute the actual web search and return real results
            return ToolOutput(
                type=ToolType.WEB_SEARCH,
                result=[
                    WebSearchResult(
                        url=f"https://example.com/search?q={query}",
                        title=f"Search results for: {query}",
                        snippet=f"Placeholder search results for query: {query}",
                        score=1.0
                    )
                ],
                raw_response=function_call
            )
        elif function_call.name == "generate_image":
            prompt = function_call.args.get("prompt", "")
            size = function_call.args.get("size", "1024x1024")
            width, height = map(int, size.split("x"))
            # Note: This is a placeholder. The actual image generation
            # happens in _make_image_generation_call
            return ToolOutput(
                type=ToolType.IMAGE_GENERATION,
                result=ImageGenerationResult(
                    image_data="",  # Will be filled by actual generation
                    format="png",
                    width=width,
                    height=height
                ),
                raw_response=function_call
            )
        return None
    
    async def chat_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Async version of chat method."""
        if messages is None:
            messages = []
        
        options = kwargs.get('options')
        if isinstance(options, LLMRequestOptions):
            if options.tools and self.supports_tools():
                kwargs['tools'] = options.tools
            if options.temperature is not None:
                kwargs['temperature'] = options.temperature
            if options.max_tokens is not None:
                kwargs['max_tokens'] = options.max_tokens
            if options.top_p is not None:
                kwargs['top_p'] = options.top_p
            if options.response_format is not None:
                kwargs['response_format'] = options.response_format
        
        return await self._make_api_call_async(messages, **kwargs)
    
    async def _make_api_call_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Make async API call to Gemini and return ChatResult."""
        # Check if we should handle tools
        tools = kwargs.pop('tools', None)
        
        # Handle special cases: image generation
        if tools and any(tool.type == ToolType.IMAGE_GENERATION or 
                        (hasattr(tool.type, 'value') and tool.type.value == "image_generation") 
                        for tool in tools):
            return await self._make_image_generation_call_async(messages, **kwargs)
        
        # Use base method to extract system prompt and messages
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in processed_messages:
            role = msg["role"]
            content = msg["content"]
            
            # Convert role names and content format
            parts = self._convert_content_to_parts(content)
            if role == "assistant":
                gemini_messages.append({"role": "model", "parts": parts})
            else:  # user role
                gemini_messages.append({"role": "user", "parts": parts})

        # Convert tools to Gemini function declarations if provided
        gemini_tools = None
        if tools and self.supports_tools():
            gemini_tools = self._convert_tools_to_gemini_format(tools)
        
        # Get the model with system instruction
        # Note: tools parameter should be in generation config, not model init
        model = self.client.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
        )

        # Use base method to extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["max_tokens", "temperature"])

        # Create generation config with tools if provided
        config_params = {
            "max_output_tokens": api_params.get("max_tokens"),
            "temperature": api_params.get("temperature"),
        }
        if gemini_tools:
            config_params["tools"] = gemini_tools
            # Set function calling mode
            config_params["tool_config"] = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="AUTO"  # Let the model decide when to use tools
                )
            )
        generation_config = self.client.GenerationConfig(**config_params)

        # Make the API call with retry logic
        response = await self._make_api_call_with_retry_async(
            model=model,
            contents=gemini_messages,
            generation_config=generation_config,
            safety_settings=kwargs.get("gemini_safety_settings"),
        )

        # Process response and handle function calls
        text = ""
        tool_outputs = []
        
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    text += part.text
                elif hasattr(part, 'function_call') and part.function_call is not None:
                    # Handle function call
                    function_output = self._process_function_call(part.function_call)
                    if function_output:
                        tool_outputs.append(function_output)

        return ChatResult(
            text=text,
            token_usage=self._create_token_usage(response),
            raw_response=response,
            tool_outputs=tool_outputs if tool_outputs else None
        )
    
    def _make_image_generation_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Handle image generation requests."""
        # Extract the prompt from messages
        prompt = ""
        for msg in messages:
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
                break
        
        try:
            # Use the image generation model with retry logic
            client = genai.Client(api_key=self.api_key)
            
            # Retry logic for image generation
            last_exception = None
            for attempt in range(self.max_retries):
                try:
                    # Use the latest flash model with image generation capabilities
                    response = client.models.generate_content(
                        model="gemini-2.0-flash-exp",  # Latest model with image generation
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=['TEXT', 'IMAGE']
                        )
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    last_exception = e
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Image generation failed, retrying in {delay}s: {e}")
                        time.sleep(delay)
                        continue
                    raise
            
            text = ""
            tool_outputs = []
            
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.text is not None:
                        text += part.text
                    elif part.inline_data is not None:
                        # Extract image data
                        image_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                        tool_outputs.append(ToolOutput(
                            type=ToolType.IMAGE_GENERATION,
                            result=ImageGenerationResult(
                                image_data=image_data,
                                format='png',
                                width=1024,  # Default values
                                height=1024
                            ),
                            raw_response=part.inline_data
                        ))
            
            return ChatResult(
                text=text,
                token_usage=None,  # Image generation doesn't provide token usage
                raw_response=response,
                tool_outputs=tool_outputs if tool_outputs else None
            )
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            # Fallback to regular chat
            return self._make_api_call(messages, **kwargs)
    
    def _convert_content_to_parts(self, content: str | list | dict) -> list:
        """Convert message content to Gemini parts format."""
        # Handle simple string content
        if isinstance(content, str):
            return [{"text": content}]
        
        # Handle list of content items (multi-modal)
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append({"text": item})
                elif isinstance(item, dict):
                    if item.get("type") == "text":
                        parts.append({"text": item.get("text", "")})
                    elif item.get("type") == "image":
                        # Handle image content
                        image_data = self._process_image_content(item)
                        if image_data:
                            parts.append(image_data)
            return parts
        
        # Handle dict content (structured format)
        if isinstance(content, dict):
            if content.get("type") == "text":
                return [{"text": content.get("text", "")}]
            elif content.get("type") == "image":
                image_data = self._process_image_content(content)
                return [image_data] if image_data else [{"text": ""}]
        
        # Default case
        return [{"text": str(content)}]
    
    def _process_image_content(self, image_item: dict) -> dict | None:
        """Process image content for Gemini API."""
        try:
            # Check for image URL
            if "url" in image_item:
                url = image_item["url"]
                if url.startswith("data:image"):
                    # Handle data URL
                    header, data = url.split(",", 1)
                    mime_type = header.split(":")[1].split(";")[0]
                    image_bytes = base64.b64decode(data)
                    return {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_bytes
                        }
                    }
                else:
                    # For remote URLs, we'd need to download the image
                    # This is a simplified implementation
                    logger.warning(f"Remote image URLs not yet supported: {url}")
                    return None
            
            # Check for base64 data
            elif "data" in image_item:
                # Assume it's base64 encoded
                mime_type = image_item.get("mime_type", "image/png")
                data = image_item["data"]
                if isinstance(data, str):
                    image_bytes = base64.b64decode(data)
                else:
                    image_bytes = data
                return {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_bytes
                    }
                }
            
            # Check for raw bytes
            elif "bytes" in image_item:
                mime_type = image_item.get("mime_type", "image/png")
                return {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_item["bytes"]
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to process image content: {e}")
        
        return None
    
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat responses token by token."""
        # Use base method to extract system prompt and messages
        system_prompt, processed_messages = self._extract_system_and_messages(messages)
        
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in processed_messages:
            role = msg["role"]
            content = msg["content"]
            
            # Convert role names and content format
            parts = self._convert_content_to_parts(content)
            if role == "assistant":
                gemini_messages.append({"role": "model", "parts": parts})
            else:  # user role
                gemini_messages.append({"role": "user", "parts": parts})
        
        # Get the model with system instruction
        model = self.client.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
        )

        # Use base method to extract allowed parameters
        api_params = self._extract_api_params(kwargs, ["max_tokens", "temperature"])

        # Create generation config
        config_params = {
            "max_output_tokens": api_params.get("max_tokens"),
            "temperature": api_params.get("temperature"),
        }
        generation_config = self.client.GenerationConfig(**config_params)

        # Make streaming API call with retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response_stream = model.generate_content(
                    contents=gemini_messages,
                    generation_config=generation_config,
                    safety_settings=kwargs.get("gemini_safety_settings"),
                    stream=True,  # Enable streaming
                )
                break  # Success, exit retry loop
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Streaming failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)  # Use async sleep for async method
                    continue
                raise
        
        # Stream the response chunks
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    
    def _make_api_call_with_retry(self, **kwargs) -> Any:
        """Make API call with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Try to make the API call
                model = kwargs.pop('model')
                return model.generate_content(**kwargs)
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "Resource has been exhausted" in error_msg or "429" in error_msg:
                    if attempt < self.max_retries - 1:
                        # Calculate exponential backoff
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(delay)
                        continue
                
                # Check if it's a safety filter rejection
                if "blocked" in error_msg.lower() or "safety" in error_msg.lower():
                    logger.warning(f"Content blocked by safety filters: {error_msg}")
                    # Return empty response instead of failing
                    return self._create_empty_response("Content was blocked by safety filters.")
                
                # For other errors, log and re-raise
                logger.error(f"Gemini API error: {error_msg}")
                raise
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error calling Gemini API: {e}")
                
                # Retry for connection errors
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Retrying after error: {e} (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                    
                raise
        
        # If we've exhausted all retries, raise the last exception
        raise last_exception
    
    def _is_retriable_error(self, error: Exception) -> bool:
        """Check if an error is retriable."""
        error_str = str(error).lower()
        retriable_keywords = [
            "timeout", "timed out", "connection", "network",
            "unavailable", "service_unavailable", "internal_error"
        ]
        return any(keyword in error_str for keyword in retriable_keywords)
    
    def _create_empty_response(self, message: str) -> Any:
        """Create an empty response object for safety filter rejections."""
        # Create a mock response object that mimics the Gemini response structure
        class MockResponse:
            def __init__(self, text):
                self.text = text
                self.candidates = [MockCandidate(text)]
                self.usage_metadata = None
        
        class MockCandidate:
            def __init__(self, text):
                self.content = MockContent(text)
        
        class MockContent:
            def __init__(self, text):
                self.parts = [MockPart(text)]
        
        class MockPart:
            def __init__(self, text):
                self.text = text
                self.function_call = None
        
        return MockResponse(message)
    
    async def _make_image_generation_call_async(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        """Async version of handle image generation requests."""
        # Extract the prompt from messages
        prompt = ""
        for msg in messages:
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
                break
        
        if not prompt:
            raise ValueError("No prompt found for image generation")
            
        # Extract the model with system instruction if present
        system_prompt, _ = self._extract_system_and_messages(messages)
        
        # Create the model with image generation capabilities
        model = self.client.GenerativeModel(
            model_name='gemini-2.0-flash-exp',  # Latest model with image generation
            system_instruction=system_prompt,
        )
        
        # Try multiple times with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=self.client.GenerationConfig(
                        response_modalities=['TEXT', 'IMAGE']
                    )
                )
                break  # Success, exit retry loop
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Image generation failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)  # Use async sleep
                    continue
                raise
        
        text = ""
        tool_outputs = []
        
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    text += part.text
                elif part.inline_data is not None:
                    # Extract image data
                    image_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                    tool_outputs.append(ToolOutput(
                        type=ToolType.IMAGE_GENERATION,
                        result=ImageGenerationResult(
                            image_data=image_data,
                            format='png',
                            width=1024,  # Default values
                            height=1024
                        ),
                        raw_response=part.inline_data
                    ))
        
        return ChatResult(
            text=text,
            token_usage=None,  # Image generation doesn't provide token usage
            raw_response=response,
            tool_outputs=tool_outputs if tool_outputs else None
        )
    
    async def _make_api_call_with_retry_async(self, **kwargs) -> Any:
        """Make async API call with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Try to make the API call
                model = kwargs.pop('model')
                return model.generate_content(**kwargs)
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "Resource has been exhausted" in error_msg or "429" in error_msg:
                    if attempt < self.max_retries - 1:
                        # Calculate exponential backoff
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(delay)  # Use async sleep
                        continue
                
                # Check if it's a safety filter rejection
                if "blocked" in error_msg.lower() or "safety" in error_msg.lower():
                    logger.warning(f"Content blocked by safety filters: {error_msg}")
                    # Return empty response instead of failing
                    return self._create_empty_response("Content was blocked by safety filters.")
                
                # For other errors, log and re-raise
                logger.error(f"Gemini API error: {error_msg}")
                raise
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error calling Gemini API: {e}")
                
                # Retry for connection errors
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Retrying after error: {e} (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)  # Use async sleep
                    continue
                    
                raise
        
        # If we've exhausted all retries, raise the last exception
        raise last_exception
    async def get_available_models(self) -> list[str]:
        """Get available Google Gemini models."""
        try:
            chat_models = []
            for model in self.client.models.list():
                if "generateContent" in model.supported_actions:
                    model_name = model.name
                    if model_name.startswith("models/"):
                        model_name = model_name[7:]
                    chat_models.append(model_name)
            
            chat_models.sort(reverse=True)
            return chat_models
            
        except Exception as e:
            logger.warning(f"Failed to fetch Google models dynamically: {e}")
            # Return default models as fallback
            return [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro-latest",
                "gemini-1.5-flash-latest",
                "gemini-1.5-flash-8b-latest",
                "gemini-1.0-pro-latest"
            ]
