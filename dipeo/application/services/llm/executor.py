"""Application service for LLM execution orchestration."""

from typing import Any, Dict, List, Optional


class LLMExecutor:
    """Orchestrates LLM calls with prepared messages.
    
    This service orchestrates between the domain layer and infrastructure,
    executing LLM calls and transforming responses into domain objects.
    """
    
    async def execute(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        api_key_id: Optional[str],
        llm_client: Any,  # Protocol for LLM client
        tools: Optional[List[Any]] = None,
    ) -> "LLMExecutionResult":
        """Execute LLM call with prepared messages.
        
        Args:
            messages: List of formatted messages
            model: LLM model identifier
            api_key_id: Optional API key identifier
            llm_client: LLM client implementation
            tools: Optional list of tools for function calling
            
        Returns:
            LLMExecutionResult with response data
        """
        # Build options if tools are provided
        options = None
        if tools:
            # Assuming LLMRequestOptions exists in models
            from dipeo.models import LLMRequestOptions
            options = LLMRequestOptions(tools=tools)
        
        # Execute LLM call
        response = await llm_client.complete(
            messages=messages,
            model=model,
            api_key_id=api_key_id,
            options=options,
        )
        
        # Extract and structure the response
        return self._build_execution_result(response)
    
    def _build_execution_result(self, response: Any) -> "LLMExecutionResult":
        """Build execution result from LLM response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Structured execution result
        """
        # Extract content
        content = response.text if hasattr(response, 'text') else str(response)
        
        # Extract usage if available
        usage = None
        if hasattr(response, 'token_usage') and response.token_usage:
            usage = {
                "input": response.token_usage.input,
                "output": response.token_usage.output,
                "total": getattr(response.token_usage, 'total', 
                               response.token_usage.input + response.token_usage.output)
            }
        
        # Extract tool outputs if available
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
        """Validate model identifier.
        
        Args:
            model: Model identifier to validate
            
        Raises:
            ValueError: If model is invalid
        """
        if not model:
            raise ValueError("Model identifier cannot be empty")
        
        # Add more validation as needed
        if not isinstance(model, str):
            raise ValueError(f"Model must be a string, got {type(model)}")


class LLMExecutionResult:
    """Result of LLM execution."""
    
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