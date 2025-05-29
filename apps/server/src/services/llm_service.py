from typing import Any, List, Optional, Tuple, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..constants import LLMService as LLMServiceEnum, COST_RATES
from ..exceptions import LLMServiceError, APIKeyError
from ..llm_adapters import ClaudeAdapter, GrokAdapter, GeminiAdapter, ChatGPTAdapter, ChatResult
from .api_key_service import APIKeyService
from ..utils.base_service import BaseService


class LLMService(BaseService):
    """Service for handling LLM interactions."""
    
    def __init__(self, api_key_service: APIKeyService):
        super().__init__()
        self.api_key_service = api_key_service
        self._adapters = {
            LLMServiceEnum.CLAUDE.value: ClaudeAdapter,
            LLMServiceEnum.GROK.value: GrokAdapter,
            LLMServiceEnum.GEMINI.value: GeminiAdapter,
            LLMServiceEnum.CHATGPT.value: ChatGPTAdapter,
            LLMServiceEnum.OPENAI.value: ChatGPTAdapter,
        }
        # Connection pool for adapters to avoid creating new instances
        self._adapter_pool = {}
    
    def _get_api_key(self, api_key_id: str) -> str:
        """Get raw API key from service."""
        try:
            api_key_data = self.api_key_service.get_api_key(api_key_id)
            return api_key_data["key"]
        except APIKeyError as e:
            raise LLMServiceError(f"Failed to get API key: {e}")
    
    def _get_adapter(self, service: str, model: str, api_key_id: str) -> Any:
        """Get the appropriate LLM adapter with connection pooling."""
        normalized_service = self.normalize_service_name(service)
        
        if normalized_service not in self._adapters:
            raise LLMServiceError(f"Unsupported LLM service: {service}")
        
        # Use pooling - cache key includes service, model, and api_key_id
        cache_key = f"{normalized_service}:{model}:{api_key_id}"
        
        if cache_key not in self._adapter_pool:
            raw_key = self._get_api_key(api_key_id)
            adapter_class = self._adapters[normalized_service]
            self._adapter_pool[cache_key] = adapter_class(model, raw_key)
        
        return self._adapter_pool[cache_key]
    
    def _get_token_counts(self, usage: Any, service: str) -> Tuple[int, int, int]:
        """Extract token counts from usage object based on service."""
        if usage is None:
            return 0, 0, 0
        
        if service == LLMServiceEnum.GEMINI.value and isinstance(usage, (list, tuple)):
            if len(usage) >= 2:
                return usage[0], usage[1], 0
            return 0, 0, 0
        
        input_tokens = (
            self.safe_get_nested(usage, 'input_tokens') or 
            self.safe_get_nested(usage, 'prompt_tokens') or 
            self.safe_get_nested(usage, 'prompt_token_count') or 0
        )
        
        output_tokens = (
            self.safe_get_nested(usage, 'output_tokens') or 
            self.safe_get_nested(usage, 'completion_tokens') or 
            self.safe_get_nested(usage, 'candidates_token_count') or 0
        )
        
        cached_tokens = 0
        if service in {LLMServiceEnum.CHATGPT.value, LLMServiceEnum.OPENAI.value}:
            cached_tokens = self.safe_get_nested(usage, 'input_tokens_details.cached_tokens', 0)
        
        return input_tokens, output_tokens, cached_tokens
    
    def calculate_cost(self, service: str, usage: Any) -> float:
        """Calculate cost for LLM usage."""
        normalized_service = self.normalize_service_name(service)
        
        if normalized_service not in COST_RATES or usage is None:
            return 0.0
        
        rates = COST_RATES[normalized_service]
        input_tokens, output_tokens, cached_tokens = self._get_token_counts(usage, normalized_service)
        
        cost = (
            (input_tokens - cached_tokens) * (rates["input"] / 1_000_000) +
            output_tokens * (rates["output"] / 1_000_000) +
            cached_tokens * (rates.get("cached", rates["input"]) / 1_000_000)
        )
        
        return cost
    
    def _extract_result_and_usage(self, result: Any) -> Tuple[str, Any]:
        """Extract text and usage from adapter result."""
        if isinstance(result, ChatResult):
            return result.text, result.usage
        # Fallback for old tuple format (can be removed later)
        elif isinstance(result, (list, tuple)):
            text = result[0] if result else ""
            usage = result[1] if len(result) > 1 else None
            return text, usage
        else:
            return result or "", None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def _call_llm_with_retry(
        self, 
        adapter: Any, 
        system_prompt: str, 
        user_prompt: str
    ) -> Any:
        """Internal method for LLM calls with retry logic."""
        return adapter.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

    async def call_llm(
        self,
        service: Optional[str],
        api_key_id: str,
        model: str,
        messages: Union[str, List[dict]],
        system_prompt: str = ""
    ) -> Tuple[str, float]:
        """Make a call to the specified LLM service with retry logic."""
        try:
            adapter = self._get_adapter(service or "chatgpt", model, api_key_id)
            
            user_prompt = str(messages) if isinstance(messages, list) else messages
            
            result = await self._call_llm_with_retry(
                adapter, system_prompt, user_prompt
            )
            
            text, usage = self._extract_result_and_usage(result)
            cost = self.calculate_cost(service or "chatgpt", usage)
            return text, cost
            
        except Exception as e:
            raise LLMServiceError(f"LLM call failed: {e}")
    
    async def get_available_models(self, service: str, api_key_id: str) -> List[str]:
        """Get available models for a service."""
        raw_key = self._get_api_key(api_key_id)
        normalized_service = self.normalize_service_name(service)
        
        if normalized_service in {LLMServiceEnum.CHATGPT.value, LLMServiceEnum.OPENAI.value}:
            try:
                import openai
                client = openai.OpenAI(api_key=raw_key)
                models = [model.id for model in client.models.list()]
                return models
            except Exception as e:
                raise LLMServiceError(f"Failed to fetch OpenAI models: {e}")
        
        return []