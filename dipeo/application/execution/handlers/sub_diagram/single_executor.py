"""Single sub-diagram executor - handles execution of individual sub-diagrams."""

import json
import logging
import uuid
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.diagram_generated.generated_nodes import SubDiagramNode

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SingleSubDiagramExecutor:
    """Executor for single sub-diagram execution with state tracking."""
    
    def __init__(self):
        """Initialize executor."""
        # Services will be set by the handler
        self._state_store = None
        self._message_router = None
        self._diagram_service = None
    
    def set_services(self, state_store, message_router, diagram_service):
        """Set services for the executor to use."""
        self._state_store = state_store
        self._message_router = message_router
        self._diagram_service = diagram_service
    
    async def execute(self, request: ExecutionRequest[SubDiagramNode]) -> NodeOutputProtocol:
        """Execute a single sub-diagram."""
        node = request.node
        
        # Check if we should skip execution when running as a sub-diagram
        if getattr(node, 'ignoreIfSub', False):
            if self._is_sub_diagram_context(request):
                return DataOutput(
                    value={"status": "skipped", "reason": "Skipped because running as sub-diagram with ignoreIfSub=true"},
                    node_id=node.id
                )
        
        try:
            # Use pre-configured services (set by handler)
            if not all([self._state_store, self._message_router, self._diagram_service]):
                raise ValueError("Required services not configured")
            
            # Load the diagram to execute
            domain_diagram = await self._load_diagram(node)
            
            # Prepare execution options
            options = {
                "variables": request.inputs or {},
                "parent_execution_id": request.execution_id,
                "is_sub_diagram": True,
                "metadata": {
                    "is_sub_diagram": True,
                    "parent_execution_id": request.execution_id
                }
            }
            
            # Create a unique execution ID for the sub-diagram
            sub_execution_id = self._create_sub_execution_id(request.execution_id)
            
            # Create the execution use case
            execute_use_case = self._create_execution_use_case(request)
            
            # Configure observers for sub-diagram execution
            filtered_observers = self._configure_observers(
                request=request,
                sub_execution_id=sub_execution_id,
                options=options
            )
            
            # Execute the sub-diagram and collect results
            execution_results, execution_error = await self._execute_sub_diagram(
                execute_use_case=execute_use_case,
                domain_diagram=domain_diagram,
                options=options,
                sub_execution_id=sub_execution_id,
                parent_observers=filtered_observers
            )
            
            # Build and return output
            return self._build_node_output(
                node=node,
                sub_execution_id=sub_execution_id,
                execution_results=execution_results,
                execution_error=execution_error
            )
            
        except Exception as e:
            logger.error(f"Error executing sub-diagram node {node.id}: {e}", exc_info=True)
            return DataOutput(
                value={"error": str(e)},
                node_id=node.id,
                metadata=json.dumps({
                    "status": "error",
                    "error": str(e)
                })
            )
    
    def _create_execution_use_case(
        self,
        request: ExecutionRequest[SubDiagramNode]
    ) -> ExecuteDiagramUseCase:
        """Create the execution use case with proper service registry."""
        from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
        
        # Get service registry and container
        service_registry = request.parent_registry
        if not service_registry:
            from dipeo.application.registry import ServiceKey, ServiceRegistry
            service_registry = ServiceRegistry()
            for service_name, service in request.services.items():
                key = ServiceKey(service_name)
                service_registry.register(key, service)
        
        container = request.parent_container
        
        return ExecuteDiagramUseCase(
            service_registry=service_registry,
            state_store=self._state_store,
            message_router=self._message_router,
            diagram_service=self._diagram_service,
            container=container
        )
    
    def _configure_observers(
        self,
        request: ExecutionRequest[SubDiagramNode],
        sub_execution_id: str,
        options: dict[str, Any]
    ) -> list[Any]:
        """Configure observers for sub-diagram execution."""
        # Get parent observers if available
        parent_observers = options.get("observers", [])
        
        # Filter observers based on their propagation settings
        from dipeo.application.execution.observers.scoped_observer import create_scoped_observers
        filtered_observers = create_scoped_observers(
            observers=parent_observers,
            parent_execution_id=request.execution_id,
            sub_execution_id=sub_execution_id,
            inherit_all=False  # Only inherit observers with propagate_to_sub=True
        )
        
        # Log sub-diagram execution start
        if request.metadata:
            request.add_metadata("sub_execution_id", sub_execution_id)
        
        return filtered_observers
    
    def _build_node_output(
        self,
        node: SubDiagramNode,
        sub_execution_id: str,
        execution_results: dict[str, Any],
        execution_error: str | None
    ) -> DataOutput:
        """Build the node output based on execution results."""
        if execution_error:
            return DataOutput(
                value={"error": execution_error},
                node_id=node.id,
                metadata=json.dumps({
                    "sub_execution_id": sub_execution_id,
                    "status": "failed",
                    "error": execution_error
                })
            )
        
        # Process output mapping
        output_value = self._process_output_mapping(node, execution_results)
        
        # Return success output
        return DataOutput(
            value=output_value,
            node_id=node.id,
            metadata=json.dumps({
                "sub_execution_id": sub_execution_id,
                "status": "completed",
                "execution_results": execution_results
            })
        )
    
    def _is_sub_diagram_context(self, request: ExecutionRequest[SubDiagramNode]) -> bool:
        """Check if we're running in a sub-diagram context."""
        # Check metadata for sub-diagram indicators
        if request.metadata:
            if request.metadata.get('parent_execution_id') or request.metadata.get('is_sub_diagram'):
                return True
        
        # Check context metadata if available
        if hasattr(request.context, 'metadata') and request.context.metadata:
            if request.context.metadata.get('is_sub_diagram') or request.context.metadata.get('parent_execution_id'):
                return True
        
        return False
    
    async def _load_diagram(self, node: SubDiagramNode) -> Any:
        """Load the diagram to execute as DomainDiagram."""
        # If diagram_data is provided directly, convert it to DomainDiagram
        if node.diagram_data:
            return await self._load_diagram_from_data(node.diagram_data)
        
        # Otherwise, load by name from storage
        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")
        
        return await self._load_diagram_from_file(node)
    
    async def _load_diagram_from_data(self, diagram_data: dict[str, Any]) -> Any:
        """Load diagram from inline data."""
        if not self._diagram_service:
            raise ValueError("Diagram service not available for conversion")
        
        import yaml
        yaml_content = yaml.dump(diagram_data, default_flow_style=False, sort_keys=False)
        return self._diagram_service.load_diagram(yaml_content)
    
    async def _load_diagram_from_file(self, node: SubDiagramNode) -> Any:
        """Load diagram from file."""
        if not self._diagram_service:
            raise ValueError("Diagram service not available")
        
        # Construct file path based on diagram name and format
        file_path = self._construct_diagram_path(node)
        
        try:
            # Use diagram service to load the diagram - returns DomainDiagram
            diagram = await self._diagram_service.load_from_file(file_path)
            return diagram
        except Exception as e:
            logger.error(f"Error loading diagram from '{file_path}': {e!s}")
            raise ValueError(f"Failed to load diagram '{node.diagram_name}': {e!s}")
    
    def _construct_diagram_path(self, node: SubDiagramNode) -> str:
        """Construct the file path for a diagram."""
        diagram_name = node.diagram_name
        
        # Determine format suffix
        format_suffix = ".light.yaml"  # Default format
        if node.diagram_format:
            format_map = {
                'light': '.light.yaml',
                'native': '.native.json',
                'readable': '.readable.yaml'
            }
            format_suffix = format_map.get(node.diagram_format, '.light.yaml')
        
        # Construct full file path
        if diagram_name.startswith('projects/'):
            return f"{diagram_name}{format_suffix}"
        elif diagram_name.startswith('codegen/'):
            return f"files/{diagram_name}{format_suffix}"
        else:
            return f"files/diagrams/{diagram_name}{format_suffix}"
    
    def _process_output_mapping(self, node: SubDiagramNode, execution_results: dict[str, Any]) -> Any:
        """Process output mapping from sub-diagram results.
        
        Returns the appropriate output based on endpoint nodes or the last output.
        """
        if not execution_results:
            return {}
        
        # Find endpoint outputs
        endpoint_outputs = self._find_endpoint_outputs(execution_results)
        
        if endpoint_outputs:
            # If there's one endpoint, return its value directly
            if len(endpoint_outputs) == 1:
                return list(endpoint_outputs.values())[0]
            # Multiple endpoints, return all
            return endpoint_outputs
        
        # No endpoints, return the last output
        return list(execution_results.values())[-1] if execution_results else {}
    
    def _find_endpoint_outputs(self, execution_results: dict[str, Any]) -> dict[str, Any]:
        """Find endpoint node outputs in execution results."""
        return {
            k: v for k, v in execution_results.items() 
            if k.startswith("endpoint") or k.startswith("end")
        }
    
    def _create_sub_execution_id(self, parent_execution_id: str) -> str:
        """Create a unique execution ID for sub-diagram."""
        return f"{parent_execution_id}_sub_{uuid.uuid4().hex[:8]}"
    
    async def _execute_sub_diagram(
        self,
        execute_use_case: "ExecuteDiagramUseCase",
        domain_diagram: Any,  # DomainDiagram
        options: dict[str, Any],
        sub_execution_id: str,
        parent_observers: list[Any]
    ) -> tuple[dict[str, Any], str | None]:
        """Execute the sub-diagram and return results and any error."""
        execution_results = {}
        execution_error = None
        
        async for update in execute_use_case.execute_diagram(
            diagram=domain_diagram,
            options=options,
            execution_id=sub_execution_id,
            interactive_handler=None,
            observers=parent_observers
        ):
            # Process execution updates
            result, error, should_break = self._process_execution_update(update, execution_results)
            
            if error:
                execution_error = error
                logger.error(f"Sub-diagram execution failed: {execution_error}")
            
            if should_break:
                break
        
        return execution_results, execution_error
    
    def _process_execution_update(
        self,
        update: dict[str, Any],
        execution_results: dict[str, Any]
    ) -> tuple[dict | None, str | None, bool]:
        """Process a single execution update.
        
        Returns: (result, error, should_break)
        """
        update_type = update.get("type", "")
        
        if update_type == "NODE_STATUS_CHANGED":
            data = update.get("data", {})
            if data.get("status") == "COMPLETED":
                node_id = data.get("node_id")
                node_output = data.get("output")
                if node_id and node_output:
                    execution_results[node_id] = node_output
                    return {node_id: node_output}, None, False
        
        elif update_type == "EXECUTION_STATUS_CHANGED":
            data = update.get("data", {})
            if data.get("status") == "COMPLETED":
                return None, None, True
            elif data.get("status") == "FAILED":
                error = data.get("error") or f"Execution failed (node_id: {data.get('node_id', 'unknown')})"
                return None, error, True
        
        # Legacy support for old update types
        elif update_type == "node_complete":
            node_id = update.get("node_id")
            node_output = update.get("output")
            if node_id and node_output:
                execution_results[node_id] = node_output
                return {node_id: node_output}, None, False
        
        elif update_type == "execution_complete":
            return None, None, True
        
        elif update_type == "execution_error":
            error = update.get("error") or f"Execution failed with status: {update.get('status', 'unknown')}"
            return None, error, True
        
        return None, None, False