"""Single sub-diagram executor - handles execution of individual sub-diagrams."""

from typing import TYPE_CHECKING, Any, Optional
import json
import logging
import uuid

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
from dipeo.diagram_generated.generated_nodes import SubDiagramNode
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.application.registry.keys import (
    STATE_STORE,
    MESSAGE_ROUTER,
    DIAGRAM_SERVICE_NEW,
)

if TYPE_CHECKING:
    from dipeo.application.registry import ServiceRegistry, ServiceKey

log = logging.getLogger(__name__)


class SingleSubDiagramExecutor:
    """Executor for single sub-diagram execution."""
    
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
            # Get required services
            state_store = request.services.resolve(STATE_STORE)
            message_router = request.services.resolve(MESSAGE_ROUTER)
            diagram_service = request.services.resolve(DIAGRAM_SERVICE_NEW)
            
            if not all([state_store, message_router]):
                raise ValueError("Required services not available")
            
            # Load the diagram to execute
            domain_diagram = await self._load_diagram(node, diagram_service)
            
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
            
            # Get service registry and container
            service_registry = request.parent_registry
            if not service_registry:
                from dipeo.application.registry import ServiceRegistry, ServiceKey
                service_registry = ServiceRegistry()
                for service_name, service in request.services.items():
                    key = ServiceKey(service_name)
                    service_registry.register(key, service)
            
            container = request.parent_container
            
            # Create the execution use case
            execute_use_case = ExecuteDiagramUseCase(
                service_registry=service_registry,
                state_store=state_store,
                message_router=message_router,
                diagram_service=diagram_service,
                container=container
            )
            
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
            
            # Execute the sub-diagram and collect results
            execution_results, execution_error = await self._execute_sub_diagram(
                execute_use_case=execute_use_case,
                domain_diagram=domain_diagram,
                options=options,
                sub_execution_id=sub_execution_id,
                parent_observers=filtered_observers
            )
            
            # Handle execution error
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
            
        except Exception as e:
            log.error(f"Error executing sub-diagram node {node.id}: {e}", exc_info=True)
            return DataOutput(
                value={"error": str(e)},
                node_id=node.id,
                metadata=json.dumps({
                    "status": "error",
                    "error": str(e)
                })
            )
    
    def _is_sub_diagram_context(self, request: ExecutionRequest[SubDiagramNode]) -> bool:
        """Check if we're running in a sub-diagram context."""
        is_sub_diagram = False
        
        # Primary detection: Check metadata for sub-diagram indicators
        if request.metadata:
            if request.metadata.get('parent_execution_id'):
                is_sub_diagram = True
            if request.metadata.get('is_sub_diagram'):
                is_sub_diagram = True
        
        # Secondary detection: Check context metadata if available
        if hasattr(request.context, 'metadata') and request.context.metadata:
            if request.context.metadata.get('is_sub_diagram'):
                is_sub_diagram = True
            if request.context.metadata.get('parent_execution_id'):
                is_sub_diagram = True
        
        return is_sub_diagram
    
    async def _load_diagram(self, node: SubDiagramNode, diagram_service: Any) -> Any:
        """Load the diagram to execute as DomainDiagram."""
        # If diagram_data is provided directly, convert it to DomainDiagram
        if node.diagram_data:
            # diagram_data is a dict that needs conversion
            # Use the diagram service to convert it
            if diagram_service:
                import yaml
                yaml_content = yaml.dump(node.diagram_data, default_flow_style=False, sort_keys=False)
                return diagram_service.load_diagram(yaml_content)
            else:
                raise ValueError("Diagram service not available for conversion")
        
        # Otherwise, load by name from storage
        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")
        
        if not diagram_service:
            raise ValueError("Diagram service not available")
        
        # Construct file path based on diagram name and format
        diagram_name = node.diagram_name
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
            file_path = f"{diagram_name}{format_suffix}"
        elif diagram_name.startswith('codegen/'):
            file_path = f"files/{diagram_name}{format_suffix}"
        else:
            file_path = f"files/diagrams/{diagram_name}{format_suffix}"
        
        try:
            # Use diagram service to load the diagram - returns DomainDiagram
            diagram = await diagram_service.load_from_file(file_path)
            return diagram
            
        except Exception as e:
            log.error(f"Error loading diagram from '{file_path}': {str(e)}")
            raise ValueError(f"Failed to load diagram '{node.diagram_name}': {str(e)}")
    
    def _process_output_mapping(self, node: SubDiagramNode, execution_results: dict[str, Any]) -> dict[str, Any]:
        """Process output mapping from sub-diagram results."""
        # Simple output - just return all results
        if not execution_results:
            return {}
        
        # Find endpoint outputs
        endpoint_outputs = {
            k: v for k, v in execution_results.items() 
            if k.startswith("endpoint") or k.startswith("end")
        }
        
        if endpoint_outputs:
            # If there's one endpoint, return its value directly
            if len(endpoint_outputs) == 1:
                return list(endpoint_outputs.values())[0]
            # Multiple endpoints, return all
            return endpoint_outputs
        
        # No endpoints, return the last output
        return list(execution_results.values())[-1] if execution_results else {}
    
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
    ) -> tuple[dict[str, Any], Optional[str]]:
        """Execute the sub-diagram and return results and any error."""
        execution_results = {}
        execution_error = None
        
        update_count = 0
        
        async for update in execute_use_case.execute_diagram(
            diagram=domain_diagram,
            options=options,
            execution_id=sub_execution_id,
            interactive_handler=None,
            observers=parent_observers
        ):
            update_count += 1
            
            # Process execution updates
            update_type = update.get("type", "")
            
            if update_type == "NODE_STATUS_CHANGED":
                # Check if this is a node completion
                data = update.get("data", {})
                if data.get("status") == "COMPLETED":
                    node_id = data.get("node_id")
                    node_output = data.get("output")
                    if node_id and node_output:
                        execution_results[node_id] = node_output
            
            elif update_type == "EXECUTION_STATUS_CHANGED":
                # Check if execution is complete
                data = update.get("data", {})
                if data.get("status") == "COMPLETED":
                    break
                elif data.get("status") == "FAILED":
                    execution_error = data.get("error")
                    if not execution_error:
                        # Try to get more context from the data
                        execution_error = f"Execution failed (node_id: {data.get('node_id', 'unknown')})"
                    log.error(f"Sub-diagram execution failed: {execution_error}")
                    break
            
            # Legacy support for old update types
            elif update_type == "node_complete":
                node_id = update.get("node_id")
                node_output = update.get("output")
                if node_id and node_output:
                    execution_results[node_id] = node_output
            
            elif update_type == "execution_complete":
                break
            
            elif update_type == "execution_error":
                execution_error = update.get("error")
                if not execution_error:
                    # If no error message provided, try to get status for more context
                    status = update.get("status", "unknown")
                    execution_error = f"Execution failed with status: {status}"
                log.error(f"Sub-diagram execution failed: {execution_error}")
                break
        
        return execution_results, execution_error