import asyncio
import logging
import time
from typing import Any

from openai import OpenAI

from dipeo.diagram_generated import ChatResult, ToolOutput

from .phase_aware import PhaseAwareAdapter
from .common import (
    ExecutionPhase,
    MemorySelectionOutput,
    convert_tools_to_api_format,
    process_tool_outputs,
    process_structured_output,
    create_empty_response,
)

logger = logging.getLogger(__name__)


class ChatGPTAdapter(PhaseAwareAdapter):
    """Adapter for OpenAI GPT models (sync only)."""
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        super().__init__(model_name, api_key, base_url)
        self.max_retries = 3
        self.retry_delay = 1.0

    def _initialize_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def supports_tools(self) -> bool:
        supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini']
        return any(model in self.model_name for model in supported_models)
    
    def supports_response_api(self) -> bool:
        return 'gpt-4o-mini' in self.model_name or 'gpt-4.1' in self.model_name
    
    def _is_temperature_unsupported_model(self) -> bool:
        """Check if the model doesn't support temperature parameter."""
        return 'gpt-5' in self.model_name

    def _prepare_api_request(self, messages: list[dict[str, str]], **kwargs) -> tuple[list[dict], list[dict], dict]:
        """Prepare API request parameters."""
        # Use base class method for common processing
        processed_messages, api_params, execution_phase = self.prepare_request_with_phase(messages, **kwargs)
        
        if not processed_messages:
            logger.warning("No messages provided to OpenAI API call")
            return [], [], {}
        
        # Extract tools and convert to OpenAI format
        tools = self.extract_tools(api_params)
        api_tools = convert_tools_to_api_format(tools, provider="openai")
        
        if api_tools:
            logger.debug(f"API tools: {api_tools}")
        
        # Handle temperature parameter
        allowed_params = []
        if not self._is_temperature_unsupported_model():
            allowed_params.append("temperature")
        
        # Clean up api_params to only include allowed parameters
        clean_params = self._extract_api_params(api_params, allowed_params)
        
        # Check if we need structured output
        text_format = api_params.get('text_format')
        pydantic_model = self.should_use_structured_output(execution_phase, text_format)
        if pydantic_model:
            clean_params["_pydantic_model"] = pydantic_model
            logger.debug(f"Using structured output with model: {pydantic_model.__name__}")
        
        return processed_messages, api_tools, clean_params
    
    def _process_api_response(self, response: Any) -> tuple[str, list[ToolOutput] | None, dict]:
        """Process API response to extract text, tool outputs, and token usage."""
        # Handle structured output
        if hasattr(response, 'output_parsed'):
            text = process_structured_output(response.output_parsed)
        elif hasattr(response, 'parsed'):
            text = process_structured_output(response.parsed)
        else:
            text = getattr(response, 'output_text', '')
        
        # Process tool outputs
        tool_outputs = process_tool_outputs(response, provider="openai")
        
        # Create token usage
        token_usage = self._create_token_usage(
            response,
            input_field="input_tokens",
            output_field="output_tokens"
        )
        
        return text, tool_outputs, token_usage
    
    def _make_api_call(self, messages: list[dict[str, str]], **kwargs) -> ChatResult:
        # Prepare request
        input_messages, api_tools, api_params = self._prepare_api_request(messages, **kwargs)
        if not input_messages:
            return ChatResult(text='', raw_response=None)
        # Make response API call with retry logic
        response = self._make_api_call_with_retry(
            input_messages=input_messages,
            api_tools=api_tools,
            api_params=api_params
        )
        
        # Process response
        text, tool_outputs, token_usage = self._process_api_response(response)
        
        return ChatResult(
            text=text,
            token_usage=token_usage,
            raw_response=response,
            tool_outputs=tool_outputs
        )
    
    def _make_api_call_with_retry(self, input_messages: list, api_tools: list, api_params: dict) -> Any:
        """Make API call with exponential backoff retry logic (sync version)."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Check if we have a Pydantic model for structured output
                pydantic_model = api_params.pop('_pydantic_model', None)
                
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
                
                # Try to make the API call
                if pydantic_model:
                    logger.debug(f"Using responses.parse() with Pydantic model: {pydantic_model.__name__}")
                    create_params['text_format'] = pydantic_model
                    return self.client.responses.parse(**create_params)
                else:
                    return self.client.responses.create(**create_params)
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < self.max_retries - 1:
                        # Calculate exponential backoff
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(delay)
                        continue
                
                # Log error
                logger.error(f"OpenAI API error: {error_msg}")
                
                # Retry for connection errors
                if attempt < self.max_retries - 1 and self._is_retriable_error(e):
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Retrying after error: {e} (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                    
                # For final attempt or non-retriable errors, return empty result
                if attempt == self.max_retries - 1:
                    logger.error(f"All retry attempts exhausted for OpenAI API")
                    return self._create_empty_response(f"API call failed after {self.max_retries} attempts")
        
        # If we've exhausted all retries, return empty response
        return self._create_empty_response("Failed to get response from OpenAI API")
    
    def _is_retriable_error(self, error: Exception) -> bool:
        """Check if an error is retriable."""
        error_str = str(error).lower()
        retriable_keywords = [
            "timeout", "timed out", "connection", "network",
            "unavailable", "service_unavailable", "internal_error"
        ]
        return any(keyword in error_str for keyword in retriable_keywords)
    
    def _create_empty_response(self, message: str) -> Any:
        """Create an empty response object for error cases."""
        return create_empty_response(message)
    
    
    async def get_available_models(self) -> list[str]:
        """Get available OpenAI models."""
        try:
            models_response = await asyncio.to_thread(self.client.models.list)
            
            chat_models = []
            for model in models_response.data:
                model_id = model.id
                if any(prefix in model_id for prefix in ["gpt-", "o1", "o3", "chatgpt"]):
                    chat_models.append(model_id)
            
            # Ensure gpt-5-nano-2025-08-07 is included
            if "gpt-5-nano-2025-08-07" not in chat_models:
                chat_models.append("gpt-5-nano-2025-08-07")
            
            chat_models.sort(reverse=True)
            return chat_models
            
        except Exception as e:
            logger.warning(f"Failed to fetch OpenAI models dynamically: {e}")
            # Return default models as fallback
            return [
                "gpt-5-nano-2025-08-07",
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ]
