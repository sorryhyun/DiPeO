"""Handler for SubDiagramNode - executes diagrams within diagrams."""

from typing import TYPE_CHECKING, Any, Optional
import asyncio
import logging

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import SubDiagramNode
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.models import NodeType, ExecutionStatus
from dipeo.models.models import SubDiagramNodeData

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry
    from dipeo.infra.persistence.diagram.diagram_loader import DiagramLoaderAdapter

log = logging.getLogger(__name__)


@register_handler
class SubDiagramNodeHandler(TypedNodeHandler[SubDiagramNode]):
    """Handler for executing diagrams within diagrams.
    
    This handler allows a diagram to execute another diagram as a node,
    passing inputs and receiving outputs from the sub-diagram execution.
    """
    
    @property
    def requires_services(self) -> list[str]:
        return ["state_store", "message_router", "diagram_loader"]
    
    @property
    def node_class(self) -> type[SubDiagramNode]:
        return SubDiagramNode
    
    @property
    def node_type(self) -> str:
        return NodeType.sub_diagram.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return SubDiagramNodeData
    
    @property
    def description(self) -> str:
        return "Execute another diagram as a node within the current diagram"
    
    def validate(self, request: ExecutionRequest[SubDiagramNode]) -> Optional[str]:
        """Validate the sub-diagram node configuration."""
        node = request.node
        
        # Validate that either diagram_name or diagram_data is provided
        if not node.diagram_name and not node.diagram_data:
            return "Either diagram_name or diagram_data must be specified"
        
        # If both are provided, warn but continue
        if node.diagram_name and node.diagram_data:
            log.warning(f"Both diagram_name and diagram_data provided for node {node.id}. diagram_data will be used.")
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[SubDiagramNode]) -> NodeOutputProtocol:
        """Execute the sub-diagram node."""
        node = request.node
        context = request.context
        
        try:
            # Get required services
            state_store = request.services.get("state_store")
            message_router = request.services.get("message_router")
            diagram_loader = request.services.get("diagram_loader")
            
            if not all([state_store, message_router]):
                raise ValueError("Required services not available")
            
            # Load the diagram to execute
            diagram_data = await self._load_diagram(node, diagram_loader)
            
            # Prepare execution options
            options = {
                "variables": {},  # Initialize with empty variables
                "parent_execution_id": request.execution_id,
                "is_sub_diagram": True
            }
            
            # Pass inputs as variables to the sub-diagram
            if request.inputs:
                # Flatten inputs into variables
                for key, value in request.inputs.items():
                    if isinstance(value, dict) and "value" in value:
                        # Extract value from wrapped inputs
                        options["variables"][key] = value["value"]
                    else:
                        options["variables"][key] = value
            
            # Add any additional variables from the node configuration
            if node.input_mapping:
                for target_key, source_key in node.input_mapping.items():
                    if source_key in request.inputs:
                        value = request.inputs[source_key]
                        if isinstance(value, dict) and "value" in value:
                            options["variables"][target_key] = value["value"]
                        else:
                            options["variables"][target_key] = value
            
            # Create a unique execution ID for the sub-diagram
            import uuid
            sub_execution_id = f"{request.execution_id}_sub_{uuid.uuid4().hex[:8]}"
            
            # Execute the sub-diagram using the execute_diagram use case
            from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
            from dipeo.application.unified_service_registry import UnifiedServiceRegistry
            
            # Create a service registry for the sub-diagram execution
            # We need to get the registry from the execution context
            service_registry = context.get_service_registry() if hasattr(context, 'get_service_registry') else None
            
            if not service_registry:
                # Fallback: create minimal registry with available services
                service_registry = UnifiedServiceRegistry()
                service_registry.register("state_store", state_store)
                service_registry.register("message_router", message_router)
                if diagram_loader:
                    service_registry.register("diagram_loader", diagram_loader)
                    # Also register as diagram_storage_service for backward compatibility
                    service_registry.register("diagram_storage_service", diagram_loader)
            
            execute_use_case = ExecuteDiagramUseCase(
                service_registry=service_registry,
                state_store=state_store,
                message_router=message_router
            )
            
            # Log sub-diagram execution start
            log.info(f"Starting sub-diagram execution: {sub_execution_id}")
            request.add_metadata("sub_execution_id", sub_execution_id)
            
            # Collect results from the sub-diagram execution
            execution_results = {}
            execution_error = None
            
            async for update in execute_use_case.execute_diagram(
                diagram=diagram_data,
                options=options,
                execution_id=sub_execution_id,
                interactive_handler=None
            ):
                # Process execution updates
                if update.get("type") == "node_complete":
                    # Collect outputs from completed nodes
                    node_id = update.get("node_id")
                    node_output = update.get("output")
                    if node_id and node_output:
                        execution_results[node_id] = node_output
                
                elif update.get("type") == "execution_complete":
                    log.info(f"Sub-diagram execution completed: {sub_execution_id}")
                    break
                
                elif update.get("type") == "execution_error":
                    execution_error = update.get("error", "Unknown error")
                    log.error(f"Sub-diagram execution failed: {execution_error}")
                    break
            
            # Handle execution error
            if execution_error:
                return DataOutput(
                    value={"error": execution_error},
                    node_id=node.id,
                    metadata={
                        "sub_execution_id": sub_execution_id,
                        "status": "failed",
                        "error": execution_error
                    }
                )
            
            # Process output mapping
            output_value = self._process_output_mapping(node, execution_results)
            
            # Return success output
            return DataOutput(
                value=output_value,
                node_id=node.id,
                metadata={
                    "sub_execution_id": sub_execution_id,
                    "status": "completed",
                    "execution_results": execution_results
                }
            )
            
        except Exception as e:
            log.error(f"Error executing sub-diagram node {node.id}: {e}", exc_info=True)
            return DataOutput(
                value={"error": str(e)},
                node_id=node.id,
                metadata={
                    "status": "error",
                    "error": str(e)
                }
            )
    
    async def _load_diagram(self, node: SubDiagramNode, diagram_loader: Optional["DiagramLoaderAdapter"]) -> dict[str, Any]:
        """Load the diagram to execute."""
        # If diagram_data is provided directly, use it
        if node.diagram_data:
            return node.diagram_data
        
        # Otherwise, load by name from storage
        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")
        
        # Check if diagram loader is available
        if not diagram_loader:
            raise ValueError("Diagram loader not available")
        
        # Load the diagram
        # The diagram name might include format suffix like .light.yaml
        diagram_name = node.diagram_name
        
        # Try to load from different formats
        formats = [".native.json", ".light.yaml", ".readable.yaml"]
        domain_diagram = None
        
        for fmt in formats:
            try:
                file_path = f"files/diagrams/{diagram_name}"
                if not diagram_name.endswith(fmt):
                    file_path = f"files/diagrams/{diagram_name}{fmt}"
                
                # Use the diagram loader to load from file
                domain_diagram = await diagram_loader.load_from_file(file_path)
                break
            except Exception:
                continue
        
        if not domain_diagram:
            raise ValueError(f"Diagram '{diagram_name}' not found in any format")
        
        # Convert domain diagram to dict for execution
        # The diagram loader returns a DomainDiagram, we need a dict
        from dipeo.domain.diagram.utils import domain_diagram_to_dict
        return domain_diagram_to_dict(domain_diagram)
    
    def _process_output_mapping(self, node: SubDiagramNode, execution_results: dict[str, Any]) -> dict[str, Any]:
        """Process output mapping from sub-diagram results."""
        output = {}
        
        # If no output mapping specified, return all results
        if not node.output_mapping:
            return {"results": execution_results}
        
        # Apply output mapping
        for output_key, source_path in node.output_mapping.items():
            # source_path might be like "node_id.output_field"
            parts = source_path.split(".", 1)
            
            if len(parts) == 1:
                # Direct node output
                node_id = parts[0]
                if node_id in execution_results:
                    output[output_key] = execution_results[node_id]
            else:
                # Nested field access
                node_id, field_path = parts
                if node_id in execution_results:
                    result = execution_results[node_id]
                    
                    # Navigate to the field
                    try:
                        value = result
                        for field in field_path.split("."):
                            if isinstance(value, dict):
                                value = value.get(field)
                            else:
                                value = None
                                break
                        
                        if value is not None:
                            output[output_key] = value
                    except Exception as e:
                        log.warning(f"Failed to extract field {field_path} from node {node_id}: {e}")
        
        # Include default output if specified
        if "default" not in output and execution_results:
            # Try to find endpoint nodes or the last executed node
            endpoint_outputs = {
                k: v for k, v in execution_results.items() 
                if k.startswith("endpoint") or k.startswith("end")
            }
            
            if endpoint_outputs:
                # Use the first endpoint output as default
                output["default"] = list(endpoint_outputs.values())[0]
            else:
                # Use the last output as default
                output["default"] = list(execution_results.values())[-1]
        
        return output
    
    def post_execute(
        self,
        request: ExecutionRequest[SubDiagramNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log sub-diagram execution."""
        # Log execution details if in debug mode
        if request.metadata.get("debug"):
            sub_execution_id = request.metadata.get("sub_execution_id", "unknown")
            print(f"[SubDiagramNode] Executed sub-diagram with ID: {sub_execution_id}")
        
        return output