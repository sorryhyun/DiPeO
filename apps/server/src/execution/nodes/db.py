"""DB node executor for data source operations."""

import structlog
from typing import Any, Dict, List, Tuple

from .base import BaseNodeExecutor
from ..state import ExecutionState
from ...db_blocks import run_db_block

logger = structlog.get_logger(__name__)


class DBNodeExecutor(BaseNodeExecutor):
    """Executes DB nodes for data source operations.
    
    DB nodes handle file reading, code evaluation, and other
    data source operations.
    """
    
    async def execute(
        self, 
        node: dict, 
        vars_map: Dict[str, Any], 
        inputs: List[Any],
        state: ExecutionState,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a DB node.
        
        Args:
            node: Node configuration with DB operation details
            vars_map: Variable mappings (unused for DB nodes)
            inputs: Input values from incoming arrows
            state: Current execution state
            **kwargs: Additional arguments (unused)
            
        Returns:
            Tuple of (data_result, 0.0)
        """
        node_id = self.get_node_id(node)
        data = self.get_node_data(node)
        
        logger.debug(
            "executing_db_node",
            node_id=node_id,
            data=data
        )
        
        try:
            # DB nodes use inputs directly
            result = await run_db_block(data, inputs)
            
            logger.info(
                "db_node_executed",
                node_id=node_id,
                has_result=result is not None,
                result_type=type(result).__name__ if result is not None else None
            )
            
            return result, 0.0
            
        except Exception as e:
            logger.error(
                "db_node_execution_failed",
                node_id=node_id,
                error=str(e),
                exc_info=True
            )
            raise