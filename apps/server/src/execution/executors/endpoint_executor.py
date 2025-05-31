"""Endpoint node executor for terminal nodes."""

from typing import Any, Dict, Tuple, Optional
import logging

from .base_executor import BaseExecutor
from ..core.execution_context import ExecutionContext
from ..core.skip_manager import SkipManager

logger = logging.getLogger(__name__)


class EndpointExecutor(BaseExecutor):
    """Executor for Endpoint nodes - marks diagram termination points."""
    
    def __init__(self, context: ExecutionContext, llm_service=None, memory_service=None):
        """Initialize the endpoint executor."""
        super().__init__(context, llm_service, memory_service)
    
    async def validate_inputs(
        self,
        node: Dict[str, Any],
        context: ExecutionContext
    ) -> Optional[str]:
        """Validate Endpoint node inputs.
        
        Args:
            node: The node configuration
            context: The execution context
            
        Returns:
            Always None - endpoint nodes accept any inputs
        """
        return None
    
    async def execute(
        self,
        node: Dict[str, Any],
        context: ExecutionContext,
        skip_manager: SkipManager,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute an Endpoint node.
        
        Args:
            node: The node configuration
            context: The execution context
            skip_manager: The skip manager (not used here)
            **kwargs: Additional arguments
            
        Returns:
            Tuple of (result, 0.0) - endpoint nodes have no cost
        """
        # Prepare inputs
        inputs = self._prepare_inputs(node, context)
        
        # Convert inputs to list format
        input_list = []
        for key, value in inputs.items():
            if value is not None:
                input_list.append(value)
        
        # Endpoint nodes collect their inputs as results
        result = input_list[0] if input_list and len(input_list) == 1 else input_list
        
        logger.info(f"Endpoint node {node['id']} reached with {len(input_list) if input_list else 0} inputs")
        
        # Check if file save is requested
        data = node.get('data', {})
        if data.get('saveToFile'):
            await self._save_to_file(result, data, node['id'])
        
        return result, 0.0
    
    async def _save_to_file(self, result: Any, data: dict, node_id: str) -> None:
        """Save result to file if configured."""
        file_path = data.get('filePath')
        if not file_path:
            logger.warning(f"Endpoint node {node_id} has saveToFile enabled but no filePath specified")
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
            await file_service.write(file_path, content, relative_to='base')
            logger.info(f"Endpoint node {node_id} saved result to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save endpoint result to file: {e}")
            # Don't raise - file save failure shouldn't stop execution