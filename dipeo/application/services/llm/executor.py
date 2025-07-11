# Application service for LLM execution orchestration.

from typing import Any, Dict, List, Optional


class LLMExecutor:
    
    async def execute(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        api_key_id: Optional[str],
        llm_client: Any,  # Protocol for LLM client
        tools: Optional[List[Any]] = None,
    ) -> "LLMExecutionResult":
        options = None
        if tools:
            from dipeo.models import LLMRequestOptions
            options = LLMRequestOptions(tools=tools)
        
        response = await llm_client.complete(
            messages=messages,
            model=model,
            api_key_id=api_key_id,
            options=options,
        )
        
        return self._build_execution_result(response)
    
    def _build_execution_result(self, response: Any) -> "LLMExecutionResult":
        content = response.text if hasattr(response, 'text') else str(response)
        
        usage = None
        if hasattr(response, 'token_usage') and response.token_usage:
            usage = {
                "input": response.token_usage.input,
                "output": response.token_usage.output,
                "total": getattr(response.token_usage, 'total', 
                               response.token_usage.input + response.token_usage.output)
            }
        
        tool_outputs = None
        if hasattr(response, 'tool_outputs') and response.tool_outputs:
            tool_outputs = [
                output.model_dump() for output in response.tool_outputs
            ]
        
        return LLMExecutionResult(
            content=content,
            usage=usage,
            tool_outputs=tool_outputs,
            raw_response=response,
        )
    
    def validate_model(self, model: str) -> None:
        if not model:
            raise ValueError("Model identifier cannot be empty")
        
        if not isinstance(model, str):
            raise ValueError(f"Model must be a string, got {type(model)}")


class LLMExecutionResult:
    
    def __init__(
        self,
        content: str,
        usage: Optional[Dict[str, int]] = None,
        tool_outputs: Optional[List[Dict[str, Any]]] = None,
        raw_response: Optional[Any] = None,
    ):
        self.content = content
        self.usage = usage
        self.tool_outputs = tool_outputs
        self.raw_response = raw_response