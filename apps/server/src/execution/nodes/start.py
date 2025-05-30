"""Start node executor for diagram entry points."""

import structlog
from typing import Any, Dict, List, Tuple

from .base import BaseNodeExecutor
from ..state import ExecutionState

logger = structlog.get_logger(__name__)


class StartNodeExecutor(BaseNodeExecutor):
    """Executes Start nodes which serve as diagram entry points.
    
    Start nodes don't perform any operations but mark the
    beginning of execution flow.
    """
    
    async def execute(
        self, 
        node: dict, 
        vars_map: Dict[str, Any], 
        inputs: List[Any],
        state: ExecutionState,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a Start node.
        
        Args:
            node: Node configuration
            vars_map: Variable mappings (unused)
            inputs: Input values (should be empty)
            state: Current execution state
            **kwargs: Additional arguments (unused)
            
        Returns:
            Tuple of (None, 0.0)
        """
        node_id = self.get_node_id(node)
        
        logger.info(
            "start_node_executed",
            node_id=node_id
        )
        
        # Start nodes don't produce output or cost
        return None, 0.0