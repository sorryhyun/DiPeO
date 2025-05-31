"""
Endpoint node executor for terminal nodes.
Marks the end of execution paths and collects results.
"""
from typing import Any, Dict, Optional
import logging

from .base_executor import BaseExecutor
from ...constants import NodeType

logger = logging.getLogger(__name__)


class EndpointExecutor(BaseExecutor):
    """Executes Endpoint nodes which mark diagram termination points."""
    
    node_type = NodeType.ENDPOINT
    
    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Validate Endpoint node inputs."""
        # Endpoint nodes accept any inputs
        pass
    
    async def execute_node(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Endpoint node logic."""
        # Prepare inputs
        input_list = self._prepare_inputs(inputs)
        
        # Endpoint nodes collect their inputs as results
        result = input_list[0] if input_list and len(input_list) == 1 else input_list
        
        logger.info(f"Endpoint node {self.node_id} reached with {len(input_list) if input_list else 0} inputs")
        
        # Check if file save is requested
        data = self.node.get('data', {})
        if data.get('saveToFile'):
            await self._save_to_file(result, data)
        
        return {
            'value': result,
            'cost': 0.0,
            'is_terminal': True  # Mark as terminal node
        }
    
    async def _save_to_file(self, result: Any, data: dict) -> None:
        """Save result to file if configured."""
        file_path = data.get('filePath')
        if not file_path:
            logger.warning(f"Endpoint node {self.node_id} has saveToFile enabled but no filePath specified")
            return
        
        try:
            from ...utils.dependencies import get_unified_file_service
            file_service = get_unified_file_service()
            
            # Convert result to string
            if isinstance(result, (dict, list)):
                import json
                content = json.dumps(result, indent=2)
            else:
                content = str(result)
            
            # Save to file
            file_service.write(file_path, content, relative_to='base')
            logger.info(f"Endpoint node {self.node_id} saved result to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save endpoint result to file: {e}")
            # Don't raise - file save failure shouldn't stop execution