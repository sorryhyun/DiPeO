"""Endpoint node executor for terminal nodes."""

import structlog
from typing import Any, Dict, List, Tuple

from .base import BaseNodeExecutor
from ..state import ExecutionState

logger = structlog.get_logger(__name__)


class EndpointNodeExecutor(BaseNodeExecutor):
    """Executes Endpoint nodes which mark diagram termination points.
    
    Endpoint nodes collect results and mark the end of an execution path.
    """
    
    async def execute(
        self, 
        node: dict, 
        vars_map: Dict[str, Any], 
        inputs: List[Any],
        state: ExecutionState,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute an Endpoint node.
        
        Args:
            node: Node configuration
            vars_map: Variable mappings (unused)
            inputs: Input values to collect as results
            state: Current execution state
            **kwargs: Additional arguments (unused)
            
        Returns:
            Tuple of (collected_inputs, 0.0)
        """
        node_id = self.get_node_id(node)
        
        # Endpoint nodes collect their inputs as results
        result = inputs[0] if inputs and len(inputs) == 1 else inputs
        
        logger.info(
            "endpoint_node_executed",
            node_id=node_id,
            num_inputs=len(inputs) if inputs else 0,
            has_result=result is not None
        )
        
        return result, 0.0