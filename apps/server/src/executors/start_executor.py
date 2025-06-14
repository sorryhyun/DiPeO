"""
Start node executor - initializes execution flow
"""

from typing import Dict, Any, TYPE_CHECKING
import time
import json

if TYPE_CHECKING:
    from ..execution_engine import Ctx as ExecutionContext

from .base_executor import BaseExecutor, ValidationResult, ExecutorResult
from .validator import validate_json_field
from .executor_utils import has_incoming_connection


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
        if has_incoming_connection(node, context):
            errors.append("Start nodes should not have incoming connections")
        
        # Check if initial data is valid JSON if provided
        properties = node.get("properties", {})
        
        # Use centralized JSON validation
        if "initialData" in properties and isinstance(properties.get("initialData"), str):
            _, json_error = validate_json_field(
                properties,
                "initialData",
                required=False
            )
            if json_error:
                # Convert error to warning since invalid JSON is allowed (treated as string)
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
            execution_time=execution_time
        )