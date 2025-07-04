import asyncio
import base64
import json
import logging
import time
from io import BytesIO
from typing import Any, AsyncIterator

from google import genai
from dipeo_domain import (
    ChatResult,
    ImageGenerationResult,
    TokenUsage,
    ToolOutput,
    ToolType,
    WebSearchResult,
)
from google.genai import types
from PIL import Image

from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseAdapter):
    """Adapter for Google Gemini models via the genai API."""

    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        # Gemini doesn't use base_url, but we accept it for consistency
        super().__init__(model_name, api_key, base_url)
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial delay in seconds

    def _initialize_client(self) -> Any:
        self.client = genai.Client(api_key=self.api_key)
        return None
    
    def supports_tools(self) -> bool:
        """Check if this model supports tool usage."""
        # Gemini models that support function calling
        supported_models = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.5-flash']
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
        
        # Extract system prompt from messages
        system_prompt = ""
        gemini_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_prompt = content
            elif role == "user":
                parts = self._convert_content_to_parts(content)
                gemini_messages.append({"role": "user", "parts": parts})
            elif role == "assistant":
                parts = self._convert_content_to_parts(content)
                gemini_messages.append({"role": "model", "parts": parts})

        # Convert tools to Gemini function declarations if provided
        gemini_tools = None
        if tools and self.supports_tools():
            gemini_tools = self._convert_tools_to_gemini_format(tools)
        
        # Get the model with system instruction
        model = self.client.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            tools=gemini_tools,
        )

        # Extract allowed parameters
        allowed_params = ["max_tokens", "temperature"]
        api_params = {
            k: v for k, v in kwargs.items() if k in allowed_params and v is not None
        }

        generation_config = self.client.GenerationConfig(
            max_output_tokens=api_params.get("max_tokens"),
            temperature=api_params.get("temperature"),
        )

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

        # Extract usage
        prompt_tokens = None
        completion_tokens = None

        usage_obj = getattr(response, "usage_metadata", None)
        if usage_obj:
            prompt_tokens = getattr(usage_obj, "prompt_token_count", None)
            completion_tokens = getattr(usage_obj, "candidates_token_count", None)

        # Create TokenUsage if we have usage data
        token_usage = None
        if prompt_tokens is not None or completion_tokens is not None:
            token_usage = TokenUsage(
                input=prompt_tokens or 0,
                output=completion_tokens or 0,
                total=(prompt_tokens or 0) + (completion_tokens or 0)
                if prompt_tokens is not None and completion_tokens is not None
                else None,
            )

        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs if tool_outputs else None,
        )
    
    def _convert_tools_to_gemini_format(self, tools: list) -> list[types.Tool]:
        """Convert DiPeO tools to Gemini function declarations."""
        function_declarations = []
        
        for tool in tools:
            tool_type = tool.type if isinstance(tool.type, str) else tool.type.value
            
            if tool_type == "web_search" or tool_type == "web_search_preview":
                # Define web search function
                function_declarations.append({
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
                })
            # Add more tool types as needed
        
        if function_declarations:
            return [types.Tool(function_declarations=function_declarations)]
        return None
    
    def _process_function_call(self, function_call) -> ToolOutput | None:
        """Process a function call from Gemini response."""
        if function_call.name == "web_search":
            # For now, return a placeholder response
            # In a real implementation, this would call an actual search API
            query = function_call.args.get("query", "")
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
        return None
    
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
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-preview-image-generation",
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
        # Extract system prompt from messages
        system_prompt = ""
        gemini_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_prompt = content
            elif role == "user":
                parts = self._convert_content_to_parts(content)
                gemini_messages.append({"role": "user", "parts": parts})
            elif role == "assistant":
                parts = self._convert_content_to_parts(content)
                gemini_messages.append({"role": "model", "parts": parts})
        
        # Get the model with system instruction
        model = self.client.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
        )

        # Extract allowed parameters
        allowed_params = ["max_tokens", "temperature"]
        api_params = {
            k: v for k, v in kwargs.items() if k in allowed_params and v is not None
        }

        generation_config = self.client.GenerationConfig(
            max_output_tokens=api_params.get("max_tokens"),
            temperature=api_params.get("temperature"),
        )

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

