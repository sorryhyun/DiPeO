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
        
        # Log execution start
        log.info(f"Executing sub_diagram: {node.label}")
        log.debug(f"Diagram name: {node.diagram_name}")
        log.debug(f"Has diagram data: {node.diagram_data is not None}")
        log.debug(f"Input mapping: {node.input_mapping}")
        log.debug(f"Output mapping: {node.output_mapping}")
        log.debug(f"Inputs: {request.inputs}")
        
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
            
            # Use the new infrastructure with parent context from ExecutionRequest
            container = request.parent_container
            service_registry = request.parent_registry
            
            # If not provided in request, fall back to runtime
            if not container and request.runtime:
                container = request.runtime._container
                log.debug(f"Got container from runtime for sub-diagram {node.id}")
            
            if not service_registry and request.runtime:
                service_registry = request.runtime._service_registry
                log.debug(f"Got service registry from runtime for sub-diagram {node.id}")
            
            # Create hierarchical service registry for sub-diagram
            if service_registry:
                # Create a child registry that can selectively override services
                sub_registry = request.create_sub_registry()
                if sub_registry:
                    service_registry = sub_registry
                    log.debug(f"Created hierarchical service registry for sub-diagram {node.id}")
            else:
                # Fallback: create minimal registry (test scenarios)
                log.warning(f"Creating minimal service registry for sub-diagram {node.id}")
                service_registry = UnifiedServiceRegistry()
                # Add all services from request.services dict
                for service_name, service in request.services.items():
                    service_registry.register(service_name, service)
                # Ensure diagram_storage_service is available
                if diagram_loader:
                    service_registry.register("diagram_storage_service", diagram_loader)
                    service_registry.register("diagram_loader", diagram_loader)
            
            # Create the execution use case with the inherited services
            execute_use_case = ExecuteDiagramUseCase(
                service_registry=service_registry,
                state_store=state_store,
                message_router=message_router,
                diagram_storage_service=diagram_loader,  # Pass diagram_loader explicitly
                container=container  # Pass container for sub-diagram isolation
            )
            
            # Try to get observers from the execution context/options
            # This requires the parent execution to pass observers via options
            parent_observers = options.get("observers", [])
            
            # Create scoped observers for sub-diagram execution
            from dipeo.application.execution.observers import create_scoped_observers
            scoped_observers = create_scoped_observers(
                observers=parent_observers,
                parent_execution_id=request.execution_id,
                sub_execution_id=sub_execution_id,
                inherit_all=True  # Can be configured via node.config if needed
            )
            
            # Log sub-diagram execution start
            log.info(f"Starting sub-diagram execution: {sub_execution_id}")
            request.add_metadata("sub_execution_id", sub_execution_id)
            
            # If we have a container, create a sub-container for this sub-diagram
            sub_container = None
            if container and hasattr(container, 'create_sub_container'):
                # Get configuration for sub-diagram isolation from node config
                config_overrides = {}
                if node.config and isinstance(node.config, dict):
                    config_overrides = node.config.get('isolation', {})
                
                # Check if we need to isolate conversation based on node configuration
                if node.isolate_conversation:
                    config_overrides['isolate_conversation'] = True
                
                try:
                    sub_container = container.create_sub_container(
                        parent_execution_id=request.execution_id,
                        sub_execution_id=sub_execution_id,
                        config_overrides=config_overrides
                    )
                    if sub_container:
                        log.info(f"Created sub-container for sub-diagram {node.id}")
                        # Update the execute_use_case to use the sub-container
                        execute_use_case.container = sub_container
                        
                        # If conversation is isolated, override the conversation service
                        if node.isolate_conversation and service_registry:
                            # Get the new conversation manager from sub-container
                            new_conversation_manager = sub_container.dynamic.conversation_manager()
                            service_registry.override('conversation_manager', new_conversation_manager)
                            service_registry.override('conversation_service', new_conversation_manager)
                            log.info(f"Isolated conversation for sub-diagram {node.id}")
                except Exception as e:
                    log.warning(f"Failed to create sub-container: {e}")
            
            # Collect results from the sub-diagram execution
            execution_results = {}
            execution_error = None
            
            async for update in execute_use_case.execute_diagram(
                diagram=diagram_data,
                options=options,
                execution_id=sub_execution_id,
                interactive_handler=None,
                observers=scoped_observers  # Pass scoped observers to sub-diagram
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
            log.debug(f"Processed output value: {output_value}")
            
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
        
        # Normalize the diagram name
        diagram_name = node.diagram_name
        
        # Remove any file extension if present
        for ext in ['.light.yaml', '.native.json', '.readable.yaml', '.yaml', '.json']:
            if diagram_name.endswith(ext):
                diagram_name = diagram_name[:-len(ext)]
                break
        
        # Use the integrated diagram service to load the diagram
        # This service handles format detection and conversion properly
        try:
            # Try to get the integrated diagram service from the file service
            file_service = getattr(diagram_loader, 'file_service', None)
            if file_service:
                # Read the diagram file directly using file service
                # Try different formats in order of preference
                formats = ['light.yaml', 'native.json', 'readable.yaml']
                
                for fmt in formats:
                    try:
                        file_path = f"files/diagrams/{diagram_name}.{fmt}"
                        result = file_service.read(file_path)
                        
                        if result.get("success") and result.get("content"):
                            content = result["content"]
                            
                            # If content is already a dict (parsed YAML/JSON), use it directly
                            if isinstance(content, dict):
                                # Validate it's a proper diagram format
                                if "nodes" in content and ("connections" in content or "flow" in content):
                                    log.info(f"Successfully loaded sub-diagram from: {file_path}")
                                    return content
                            # If content is a string, parse it based on format
                            elif isinstance(content, str):
                                if fmt.endswith('.yaml'):
                                    import yaml
                                    diagram_dict = yaml.safe_load(content)
                                elif fmt.endswith('.json'):
                                    import json
                                    diagram_dict = json.loads(content)
                                else:
                                    continue
                                
                                if isinstance(diagram_dict, dict) and "nodes" in diagram_dict:
                                    log.info(f"Successfully loaded and parsed sub-diagram from: {file_path}")
                                    return diagram_dict
                    except Exception as e:
                        log.debug(f"Failed to load {file_path}: {str(e)}")
                        continue
                
                raise ValueError(f"Unable to load diagram '{diagram_name}' in any format")
            else:
                # Fallback: try using the diagram loader's prepare_diagram method
                # This might work if it's an IntegratedDiagramService
                raise ValueError("File service not available in diagram loader")
                
        except Exception as e:
            log.error(f"Error loading diagram '{diagram_name}': {str(e)}")
            raise ValueError(f"Failed to load diagram '{diagram_name}': {str(e)}")
    
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