"""Unified executor implementation that handles all node types."""

from typing import Dict, Any, List, Optional
from pydantic import ValidationError
import time
import logging

from dipeo_domain import NodeOutput
from .types import RuntimeNodeDefinition as NodeDefinition, RuntimeExecutionContext as ExecutionContext
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecutorResult:
    """Result from executing a node."""
    output: Any = None
    error: Optional[str] = None
    node_id: str = ""
    execution_time: float = 0.0
    token_usage: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class UnifiedExecutor:
    """Unified executor that handles all node types through a registration system."""
    
    def __init__(self, service_provider: Optional[Dict[str, Any]] = None):
        self._nodes: Dict[str, NodeDefinition] = {}
        self._services: Dict[str, Any] = service_provider or {}
    
    def register(self, definition: NodeDefinition) -> None:
        """Register a node type."""
        if definition.type in self._nodes:
            logger.warning(f"Overwriting existing node type: {definition.type}")
        self._nodes[definition.type] = definition
        logger.info(f"Registered node type: {definition.type}")
    
    def register_service(self, name: str, service: Any) -> None:
        """Register a service."""
        self._services[name] = service
        logger.info(f"Registered service: {name}")
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name."""
        return self._services.get(name)
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported node types."""
        return list(self._nodes.keys())
    
    
    async def execute(
        self, 
        node: Dict[str, Any], 
        context: ExecutionContext
    ) -> ExecutorResult:
        """Execute a node with full validation and error handling."""
        node_type = node["type"]
        node_id = node.get("id", "unknown")
        
        
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
                # Simplify validation error reporting
                errors = []
                for err in e.errors():
                    field_path = ".".join(str(loc) for loc in err["loc"])
                    errors.append(f"{field_path}: {err['msg']}")
                
                return ExecutorResult(
                    error=f"Validation failed: {'; '.join(errors)}",
                    node_id=node_id,
                    metadata={"node_type": node_type, "validation_errors": e.errors()}
                )
            
            # Get required services from internal service provider
            services = {}
            missing_services = []
            for service_name in definition.requires_services:
                service = self.get_service(service_name)
                if service is None:
                    missing_services.append(service_name)
                else:
                    services[service_name] = service
            
            if missing_services:
                return ExecutorResult(
                    error=f"Missing required services: {', '.join(missing_services)}",
                    node_id=node_id
                )
            
            # Get inputs from connected nodes
            inputs = await self._get_input_values(node, context)
            
            # Execute handler with services
            start_time = time.time()
            output = await definition.handler(props, context, inputs, services)
            execution_time = time.time() - start_time
            
            # All handlers must return NodeOutput format
            if not isinstance(output, NodeOutput):
                raise RuntimeError(
                    f"Handler for node type '{node_type}' must return NodeOutput instance, "
                    f"got {type(output).__name__} instead"
                )
            
            # Extract token usage from metadata if present
            token_usage = None
            if output.metadata and "tokenUsage" in output.metadata:
                token_usage = output.metadata["tokenUsage"]
            
            result = ExecutorResult(
                output=output.value,
                error=None,
                node_id=node_id,
                execution_time=execution_time,
                token_usage=token_usage,
                metadata=output.metadata or {"node_type": node_type}
            )
            
            
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