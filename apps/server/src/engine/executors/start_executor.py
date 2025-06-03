"""
Start node executor - initializes execution flow
"""

from typing import Dict, Any
import time

from .base_executor import BaseExecutor, ValidationResult, ExecutorResult


class StartExecutor(BaseExecutor):
    """
    Start node executor that initializes the execution flow.
    Start nodes should not have incoming connections and provide initial data.
    """
    
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """Validate start node configuration"""
        errors = []
        warnings = []
        
        # Start nodes should not have incoming connections
        if self.has_incoming_connection(node, context):
            errors.append("Start nodes should not have incoming connections")
        
        # Check if initial data is valid JSON if provided
        properties = node.get("properties", {})
        initial_data = properties.get("initialData")
        
        if initial_data is not None and isinstance(initial_data, str):
            # If initial data is a string, try to parse it as JSON
            try:
                import json
                json.loads(initial_data)
            except json.JSONDecodeError:
                warnings.append("Initial data is not valid JSON, will be treated as string")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """Execute start node by returning initial data"""
        start_time = time.time()
        
        # Get initial data from node properties
        properties = node.get("properties", {})
        initial_data = properties.get("initialData", {})
        
        # If initial data is a string, try to parse it as JSON
        if isinstance(initial_data, str):
            try:
                import json
                initial_data = json.loads(initial_data)
            except json.JSONDecodeError:
                # Keep as string if not valid JSON
                pass
        
        execution_time = time.time() - start_time
        
        return ExecutorResult(
            output=initial_data,
            metadata={
                "executionTime": execution_time,
                "isStartNode": True,
                "nodeId": node.get("id"),
                "nodeType": "start"
            },
            cost=0.0,
            execution_time=execution_time
        )