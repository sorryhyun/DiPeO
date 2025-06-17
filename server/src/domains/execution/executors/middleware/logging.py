"""
Logging middleware for the unified executor system.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from ..types import ExecutorResult, ExecutionContext

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """Middleware that provides comprehensive logging for node execution."""
    
    def __init__(self, log_level: int = logging.INFO, include_properties: bool = False):
        """
        Initialize logging middleware.
        
        Args:
            log_level: Logging level (default: INFO)
            include_properties: Whether to log node properties (default: False)
        """
        self.log_level = log_level
        self.include_properties = include_properties
        self._execution_start_times: Dict[str, float] = {}
    
    async def pre_execute(self, node: Dict[str, Any], context: ExecutionContext) -> None:
        """Log information before node execution."""
        node_id = node.get("id", "unknown")
        node_type = node.get("type", "unknown")
        
        # Store start time for execution timing
        self._execution_start_times[node_id] = datetime.now().timestamp()
        
        # Build log message
        log_data = {
            "event": "node_execution_start",
            "node_id": node_id,
            "node_type": node_type,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.include_properties:
            properties = node.get("properties", {})
            # Sanitize sensitive data
            sanitized_props = self._sanitize_properties(properties)
            log_data["properties"] = sanitized_props
        
        logger.log(self.log_level, f"Starting execution of {node_type} node", 
                   extra={"structured_data": log_data})
    
    async def post_execute(
        self, 
        node: Dict[str, Any], 
        context: ExecutionContext, 
        result: ExecutorResult
    ) -> None:
        """Log information after node execution."""
        node_id = node.get("id", "unknown")
        node_type = node.get("type", "unknown")
        
        # Calculate execution time
        start_time = self._execution_start_times.pop(node_id, None)
        execution_time = result.execution_time
        if start_time and not execution_time:
            execution_time = datetime.now().timestamp() - start_time
        
        # Build log message
        log_data = {
            "event": "node_execution_complete",
            "node_id": node_id,
            "node_type": node_type,
            "success": result.error is None,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add error information if present
        if result.error:
            log_data["error"] = result.error
            if result.validation_errors:
                log_data["validation_errors"] = result.validation_errors
        
        # Add token usage if present
        if result.token_usage:
            log_data["token_usage"] = result.token_usage
        
        # Add output summary (not full output to avoid large logs)
        if result.output is not None:
            log_data["output_type"] = type(result.output).__name__
            if isinstance(result.output, str):
                log_data["output_length"] = len(result.output)
            elif isinstance(result.output, (list, dict)):
                log_data["output_size"] = len(result.output)
        
        # Log at appropriate level
        if result.error:
            logger.error(f"Failed execution of {node_type} node", 
                        extra={"structured_data": log_data})
        else:
            logger.log(self.log_level, f"Completed execution of {node_type} node", 
                       extra={"structured_data": log_data})
    
    def _sanitize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize properties to remove sensitive data."""
        sanitized = {}
        sensitive_keys = {"apikey", "password", "secret", "token", "key", "apiKeyId"}
        
        for key, value in properties.items():
            key_lower = key.lower()
            # Check if key contains sensitive words
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = self._sanitize_properties(value)
            elif isinstance(value, str) and len(value) > 100:
                # Truncate long strings
                sanitized[key] = value[:100] + "..."
            else:
                sanitized[key] = value
        
        return sanitized