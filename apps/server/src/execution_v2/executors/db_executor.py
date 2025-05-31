"""
DB node executor for data source operations.
Handles file reading, code evaluation, and other data operations.
"""
from typing import Any, Dict, Optional
import logging

from .base_executor import BaseExecutor
from ...db_blocks import run_db_block
from ...constants import NodeType, DBBlockSubType

logger = logging.getLogger(__name__)


class DBExecutor(BaseExecutor):
    """Executes DB nodes for data source operations."""
    
    node_type = NodeType.DB
    
    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Validate DB node inputs."""
        data = self.node.get('data', {})
        sub_type = data.get('subType')
        
        if not sub_type:
            raise ValueError("DB node requires 'subType' specification")
        
        if sub_type not in [st.value for st in DBBlockSubType]:
            raise ValueError(f"Invalid DB subType: {sub_type}")
        
        # Validate based on subtype
        if sub_type == DBBlockSubType.FILE.value:
            if not data.get('sourceDetails'):
                raise ValueError("File type DB node requires 'sourceDetails' with file path")
        elif sub_type == DBBlockSubType.CODE.value:
            if not data.get('sourceDetails'):
                raise ValueError("Code type DB node requires 'sourceDetails' with code snippet")
    
    async def execute_node(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the DB node logic."""
        data = self.node.get('data', {})
        
        # Prepare inputs for db_blocks
        input_list = self._prepare_inputs(inputs)
        
        try:
            # Execute DB operation
            result = await run_db_block(data, input_list)
            
            logger.info(f"DB node {self.node_id} executed successfully")
            
            return {
                'value': result,
                'cost': 0.0
            }
            
        except Exception as e:
            logger.error(f"DB node {self.node_id} execution failed: {e}")
            raise