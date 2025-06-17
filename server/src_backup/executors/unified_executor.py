"""Unified executor implementation that handles all node types."""

from typing import Dict, Any, List, Optional
from pydantic import ValidationError
import time
import logging

from .types import (
    NodeDefinition, 
    ExecutorResult, 
    ExecutionContext, 
    Middleware
)

logger = logging.getLogger(__name__)


class UnifiedExecutor:
    """Unified executor that handles all node types through a registration system."""
    
    def __init__(self):
        self._nodes: Dict[str, NodeDefinition] = {}
        self._middleware: List[Middleware] = []
    
    def register(self, definition: NodeDefinition) -> None:
        """Register a node type."""
        if definition.type in self._nodes:
            logger.warning(f"Overwriting existing node type: {definition.type}")
        self._nodes[definition.type] = definition
        logger.info(f"Registered node type: {definition.type}")
    
    def add_middleware(self, middleware: Middleware) -> None:
        """Add execution middleware."""
        self._middleware.append(middleware)
        logger.info(f"Added middleware: {type(middleware).__name__}")
    
    async def execute(
        self, 
        node: Dict[str, Any], 
        context: ExecutionContext
    ) -> ExecutorResult:
        """Execute a node with full validation and error handling."""
        node_type = node["type"]
        node_id = node.get("id", "unknown")
        
        # Apply pre-execution middleware
        for mw in self._middleware:
            try:
                await mw.pre_execute(node, context)
            except Exception as e:
                logger.error(f"Pre-execution middleware failed: {e}")
        
        try:
            # Get node definition
            definition = self._nodes.get(node_type)
            if not definition:
                return ExecutorResult(
                    error=f"Unknown node type: {node_type}",
                    node_id=node_id
                )
            
            # Validate properties with Pydantic
            try:
                props = definition.schema(**node.get("properties", {}))
            except ValidationError as e:
                return ExecutorResult(
                    error="Validation failed",
                    validation_errors=[
                        {"field": err["loc"], "message": err["msg"]} 
                        for err in e.errors()
                    ],
                    node_id=node_id
                )
            
            # Check required services
            missing_services = []
            for service in definition.requires_services:
                if not hasattr(context, service):
                    missing_services.append(service)
            
            if missing_services:
                return ExecutorResult(
                    error=f"Missing required services: {', '.join(missing_services)}",
                    node_id=node_id
                )
            
            # Get inputs from connected nodes
            inputs = await self._get_input_values(node, context)
            
            # Execute handler
            start_time = time.time()
            output = await definition.handler(props, context, inputs)
            execution_time = time.time() - start_time
            
            # Extract token usage if present
            token_usage = None
            if hasattr(output, 'token_usage'):
                token_usage = output.token_usage
            
            # Extract error if present
            error = None
            if hasattr(output, 'error'):
                error = output.error
            
            # Extract actual output
            actual_output = output
            if hasattr(output, 'output'):
                actual_output = output.output
            
            result = ExecutorResult(
                output=actual_output,
                error=error,
                node_id=node_id,
                execution_time=execution_time,
                token_usage=token_usage,
                metadata={"node_type": node_type}
            )
            
            # Apply post-execution middleware
            for mw in self._middleware:
                try:
                    await mw.post_execute(node, context, result)
                except Exception as e:
                    logger.error(f"Post-execution middleware failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Execution failed for node {node_id}: {e}", exc_info=True)
            return ExecutorResult(
                error=str(e),
                node_id=node_id,
                metadata={"node_type": node_type, "error_type": type(e).__name__}
            )
    
    async def _get_input_values(
        self, 
        node: Dict[str, Any], 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Extract input values from connected nodes."""
        inputs = {}
        
        for edge in context.edges:
            if edge["target"] == node["id"]:
                source_node_id = edge["source"]
                source_handle = edge.get("sourceHandle", "output")
                target_handle = edge.get("targetHandle", "input")
                
                # Get output from source node
                source_result = context.results.get(source_node_id, {})
                source_output = source_result.get("output")
                
                # Handle different output formats
                if isinstance(source_output, dict) and source_handle in source_output:
                    value = source_output[source_handle]
                else:
                    value = source_output
                
                inputs[target_handle] = value
        
        return inputs
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported node types."""
        return list(self._nodes.keys())
    
    def get_node_definition(self, node_type: str) -> Optional[NodeDefinition]:
        """Get definition for a specific node type."""
        return self._nodes.get(node_type)