"""Handler for SubDiagramNode - executes diagrams within diagrams."""

from typing import TYPE_CHECKING, Any, Optional
import asyncio
import logging

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
from dipeo.diagram_generated.generated_nodes import SubDiagramNode, NodeType
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.sub_diagram_model import SubDiagramNodeData

if TYPE_CHECKING:
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
        return NodeType.SUB_DIAGRAM.value
    
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
        
        # Check if batch mode is enabled
        if getattr(node, 'batch', False):
            return await self._execute_batch(request)

        try:
            # Get required services
            state_store = request.services.get("state_store")
            message_router = request.services.get("message_router")
            diagram_loader = request.services.get("diagram_loader")
            
            if not all([state_store, message_router]):
                raise ValueError("Required services not available")
            
            # Load the diagram to execute
            diagram_data = await self._load_diagram(node, diagram_loader)

            # Prepare execution options - simple like CLI does it
            options = {
                "variables": request.inputs or {},  # Pass inputs directly as variables
                "parent_execution_id": request.execution_id,
                "is_sub_diagram": True
            }

            # Create a unique execution ID for the sub-diagram
            sub_execution_id = self._create_sub_execution_id(request.execution_id)
            
            # Execute the sub-diagram using the execute_diagram use case
            from dipeo.application.unified_service_registry import UnifiedServiceRegistry
            
            # Get service registry from request or runtime
            service_registry = request.parent_registry
            if not service_registry and request.runtime:
                service_registry = request.runtime._service_registry
            
            # For tests, create minimal registry if needed
            if not service_registry:
                service_registry = UnifiedServiceRegistry()
                for service_name, service in request.services.items():
                    service_registry.register(service_name, service)
            
            # Get container from request or runtime
            container = request.parent_container
            if not container and request.runtime:
                container = request.runtime._container
            
            # Create the execution use case with the inherited services
            execute_use_case = ExecuteDiagramUseCase(
                service_registry=service_registry,
                state_store=state_store,
                message_router=message_router,
                diagram_storage_service=diagram_loader,
                container=container
            )
            
            # Get parent observers if available
            parent_observers = options.get("observers", [])
            
            # Log sub-diagram execution start
            request.add_metadata("sub_execution_id", sub_execution_id)
            
            # Execute the sub-diagram and collect results
            execution_results, execution_error = await self._execute_sub_diagram(
                execute_use_case=execute_use_case,
                diagram_data=diagram_data,
                options=options,
                sub_execution_id=sub_execution_id,
                parent_observers=parent_observers
            )

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
        
        if not diagram_loader:
            raise ValueError("Diagram loader not available")
        
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
        if diagram_name.startswith('codegen/'):
            file_path = f"files/{diagram_name}{format_suffix}"
        else:
            file_path = f"files/diagrams/{diagram_name}{format_suffix}"
        
        try:
            # Get the file service from diagram loader to read the file
            file_service = getattr(diagram_loader, 'file_service', None)
            if not file_service:
                raise ValueError("File service not available in diagram loader")
            
            # Read the diagram file
            result = file_service.read(file_path)
            if not result.get("success") or not result.get("content"):
                raise ValueError(f"Failed to read diagram file: {file_path}")
            
            content = result["content"]
            
            # If content is already a dict (parsed YAML/JSON), return it
            if isinstance(content, dict):
                return content
            
            # Otherwise parse based on format
            if file_path.endswith('.yaml'):
                import yaml
                diagram_dict = yaml.safe_load(content)
            elif file_path.endswith('.json'):
                import json
                diagram_dict = json.loads(content)
            else:
                raise ValueError(f"Unknown file format: {file_path}")
            
            return diagram_dict
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
        import uuid
        return f"{parent_execution_id}_sub_{uuid.uuid4().hex[:8]}"
    
    async def _execute_sub_diagram(
        self,
        execute_use_case: "ExecuteDiagramUseCase",
        diagram_data: dict[str, Any],
        options: dict[str, Any],
        sub_execution_id: str,
        parent_observers: list[Any]
    ) -> tuple[dict[str, Any], Optional[str]]:
        """Execute the sub-diagram and return results and any error."""
        execution_results = {}
        execution_error = None
        
        update_count = 0
        
        async for update in execute_use_case.execute_diagram(
            diagram=diagram_data,
            options=options,
            execution_id=sub_execution_id,
            interactive_handler=None,
            observers=parent_observers
        ):
            update_count += 1

            # Process execution updates
            if update.get("type") == "node_complete":
                # Collect outputs from completed nodes
                node_id = update.get("node_id")
                node_output = update.get("output")
                if node_id and node_output:
                    execution_results[node_id] = node_output
            
            elif update.get("type") == "execution_complete":
                break
            
            elif update.get("type") == "execution_error":
                execution_error = update.get("error", "Unknown error")
                log.error(f"Sub-diagram execution failed: {execution_error}")
                break
        
        return execution_results, execution_error
    
    def post_execute(
        self,
        request: ExecutionRequest[SubDiagramNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log sub-diagram execution."""
        # Log execution details if in debug mode
        if request.metadata.get("debug"):
            sub_execution_id = request.metadata.get("sub_execution_id", "unknown")

        return output
    
    async def _execute_batch(self, request: ExecutionRequest[SubDiagramNode]) -> NodeOutputProtocol:
        """Execute sub-diagram for each item in the batch."""
        node = request.node
        
        # Get batch configuration
        batch_input_key = getattr(node, 'batch_input_key', 'items')
        batch_parallel = getattr(node, 'batch_parallel', True)
        
        # Extract array from inputs
        inputs = request.inputs or {}
        
        # Check if batch_input_key is in the root level or in 'default'
        if batch_input_key in inputs:
            batch_items = inputs.get(batch_input_key, [])
        elif 'default' in inputs and isinstance(inputs['default'], dict):
            batch_items = inputs['default'].get(batch_input_key, [])
        else:
            batch_items = []
        
        if not isinstance(batch_items, list):
            log.warning(f"Batch mode enabled but '{batch_input_key}' is not a list. Treating as single item.")
            batch_items = [batch_items]

        # Prepare results collection
        results = []
        errors = []
        
        if batch_parallel:
            # Execute all items in parallel
            tasks = []
            for idx, item in enumerate(batch_items):
                # Create modified request with single item as input
                item_inputs = {'default': item, '_batch_index': idx}
                task = self._execute_batch_item(request, item_inputs, idx, len(batch_items))
                tasks.append(task)
            
            # Wait for all tasks to complete
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for idx, result in enumerate(task_results):
                if isinstance(result, Exception):
                    errors.append({
                        'index': idx,
                        'error': str(result),
                        'item': batch_items[idx] if idx < len(batch_items) else None
                    })
                else:
                    results.append(result)
        else:
            # Execute items sequentially
            for idx, item in enumerate(batch_items):
                try:
                    # Create modified request with single item as input
                    item_inputs = {'default': item, '_batch_index': idx}
                    result = await self._execute_batch_item(request, item_inputs, idx, len(batch_items))
                    results.append(result)
                except Exception as e:
                    log.error(f"Error processing batch item {idx}: {e}")
                    errors.append({
                        'index': idx,
                        'error': str(e),
                        'item': item
                    })
        
        # Compile batch results
        batch_output = {
            'total_items': len(batch_items),
            'successful': len(results),
            'failed': len(errors),
            'results': [r.value if hasattr(r, 'value') else r for r in results],
            'errors': errors if errors else None
        }
        
        # Return batch output
        return DataOutput(
            value=batch_output,
            node_id=node.id,
            metadata={
                'batch_mode': True,
                'batch_parallel': batch_parallel,
                'status': 'completed' if not errors else 'partial_failure'
            }
        )
    
    async def _execute_batch_item(self, original_request: ExecutionRequest[SubDiagramNode], 
                                  item_inputs: dict[str, Any], index: int, total: int) -> Any:
        """Execute a single item in the batch."""
        log.info(f"[BATCH SUB_DIAGRAM] Processing item {index + 1}/{total}")
        
        # Create a new node instance without batch enabled to avoid recursion
        from dataclasses import replace
        node_without_batch = replace(original_request.node, batch=False)
        
        # Create new request with modified inputs and node
        request = ExecutionRequest(
            node=node_without_batch,
            context=original_request.context,
            inputs=item_inputs,
            services=original_request.services,
            metadata=original_request.metadata,
            execution_id=original_request.execution_id,
            iteration=original_request.iteration,
            runtime=original_request.runtime,
            parent_container=original_request.parent_container,
            parent_registry=original_request.parent_registry
        )
        
        return await self.execute_request(request)