"""Executor for Start nodes."""

from typing import Any, Dict, Tuple

from .base_executor import BaseExecutor
from ..core.execution_context import ExecutionContext
from ..core.skip_manager import SkipManager


class StartExecutor(BaseExecutor):
    """Executor for Start nodes - the entry point of diagram execution."""
    
    def __init__(self, context: ExecutionContext, llm_service=None, memory_service=None):
        """Initialize the start executor."""
        super().__init__(context, llm_service, memory_service)
    
    async def execute(
        self,
        node: Dict[str, Any],
        context: ExecutionContext,
        skip_manager: SkipManager,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a Start node.
        
        Start nodes simply pass through their inputs as outputs,
        serving as the entry point for the execution flow.
        
        Args:
            node: The node configuration
            context: The execution context
            skip_manager: The skip manager (not used here)
            **kwargs: Additional arguments (may include initial inputs)
            
        Returns:
            Tuple of (inputs_dict, 0.0) - start nodes have no cost
        """
        # Get initial inputs from kwargs if provided
        initial_inputs = kwargs.get('initial_inputs', {'data':None})
        
        # Prepare any configured default values
        node_inputs = self._prepare_inputs(node, context)
        
        # Merge initial inputs with node defaults (initial inputs take precedence)
        outputs = {**node_inputs, **initial_inputs}
        
        # Start nodes have no cost
        return outputs, 0.0
    
    async def validate_inputs(
        self,
        node: Dict[str, Any],
        context: ExecutionContext
    ) -> None:
        """Start nodes don't require validation.
        
        Args:
            node: The node configuration
            context: The execution context
            
        Returns:
            Always None - start nodes are always valid
        """
        return None