"""DB node executor for data source operations."""

from typing import Any, Dict, Tuple, Optional
import logging

from .base_executor import BaseExecutor
from ..core.execution_context import ExecutionContext
from ..core.skip_manager import SkipManager
from apps.server.src.db_blocks import run_db_block
from apps.server.src.constants import DBBlockSubType

logger = logging.getLogger(__name__)


class DBExecutor(BaseExecutor):
    """Executor for DB nodes - handles data source operations."""
    
    def __init__(self, context: ExecutionContext, llm_service=None, memory_service=None):
        """Initialize the DB executor."""
        super().__init__(context, llm_service, memory_service)
    
    async def execute(
        self,
        node: Dict[str, Any],
        context: ExecutionContext,
        skip_manager: SkipManager,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a DB node.
        
        Args:
            node: The node configuration
            context: The execution context
            skip_manager: The skip manager (not used here)
            **kwargs: Additional arguments
            
        Returns:
            Tuple of (result, 0.0) - DB operations have no cost
        """
        # Prepare inputs
        inputs = self._prepare_inputs(node, context)
        data = node.get('data', {})
        
        # Convert inputs to list format for db_blocks
        input_list = []
        for key, value in inputs.items():
            if value is not None:
                input_list.append(value)
        
        try:
            # Execute DB operation
            result = await run_db_block(data, input_list)
            
            logger.info(f"DB node {node['id']} executed successfully")
            
            return result, 0.0
            
        except Exception as e:
            logger.error(f"DB node {node['id']} execution failed: {e}")
            raise
    
    async def validate_inputs(
        self,
        node: Dict[str, Any],
        context: ExecutionContext
    ) -> Optional[str]:
        """Validate DB node inputs.
        
        Args:
            node: The node configuration
            context: The execution context
            
        Returns:
            Error message if validation fails, None if valid
        """
        data = node.get('data', {})
        sub_type = data.get('subType')
        
        if not sub_type:
            return "DB node requires 'subType' specification"
        
        if sub_type not in [st.value for st in DBBlockSubType]:
            return f"Invalid DB subType: {sub_type}"
        
        # Validate based on subtype
        if sub_type == DBBlockSubType.FILE.value:
            if not data.get('sourceDetails'):
                return "File type DB node requires 'sourceDetails' with file path"
        elif sub_type == DBBlockSubType.CODE.value:
            if not data.get('sourceDetails'):
                return "Code type DB node requires 'sourceDetails' with code snippet"
        
        return None