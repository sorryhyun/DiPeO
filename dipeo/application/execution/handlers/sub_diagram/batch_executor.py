"""Batch sub-diagram executor - handles parallel execution of sub-diagrams for batch operations.

This executor implements optimizations for batch parallel execution:
1. Loads diagram once and reuses for all batch items
2. Creates lightweight execution contexts
3. Uses fire-and-forget pattern for update collection
4. Focuses on collecting only final results
"""

from typing import TYPE_CHECKING, Any, Optional
import asyncio
import logging
import uuid
from dataclasses import replace

log = logging.getLogger(__name__)

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
from dipeo.diagram_generated.generated_nodes import SubDiagramNode
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.application.registry.keys import (
    STATE_STORE,
    MESSAGE_ROUTER,
    DIAGRAM_SERVICE_NEW,
    DIAGRAM_STORAGE_SERVICE,
    PREPARE_DIAGRAM_USE_CASE,
)

if TYPE_CHECKING:
    from dipeo.application.registry import ServiceRegistry, ServiceKey


class BatchSubDiagramExecutor:
    """Executor for batch sub-diagram execution with optimizations for parallel processing."""
    
    # Default configuration for batch execution
    DEFAULT_MAX_CONCURRENT = 20  # Maximum concurrent executions
    DEFAULT_BATCH_SIZE = 100     # Maximum items to process in one batch
    
    async def execute(self, request: ExecutionRequest[SubDiagramNode]) -> NodeOutputProtocol:
        """Execute sub-diagram for each item in the batch."""
        node = request.node
        
        # Get batch configuration
        batch_input_key = getattr(node, 'batch_input_key', 'items')
        batch_parallel = getattr(node, 'batch_parallel', True)
        max_concurrent = getattr(node, 'max_concurrent', self.DEFAULT_MAX_CONCURRENT)
        
        # Extract array from inputs
        batch_items = self._extract_batch_items(request.inputs, batch_input_key)
        
        # Log batch execution start (single message for entire batch)
        if batch_items:
            log.debug(f"Starting batch execution for {len(batch_items)} items (parallel={batch_parallel})")
        
        if not batch_items:
            log.warning(f"Batch mode enabled but no items found for key '{batch_input_key}'")
            return DataOutput(
                value={'total_items': 0, 'successful': 0, 'failed': 0, 'results': [], 'errors': None},
                node_id=node.id,
                metadata={'batch_mode': True, 'batch_parallel': batch_parallel, 'status': 'completed'}
            )
        
        # Load and prepare diagram once for all batch items
        # For now, use the old implementation until ExecuteDiagramUseCase is updated
        # to work with ExecutableDiagram directly
        diagram_service = request.services.resolve(DIAGRAM_SERVICE_NEW)
        diagram_data = await self._load_diagram_fallback(node, diagram_service)
        
        # Prepare base execution context
        base_context = await self._prepare_base_context(request)
        
        # Execute batch items
        if batch_parallel:
            results, errors = await self._execute_parallel(
                batch_items, request, diagram_data, base_context, max_concurrent
            )
        else:
            results, errors = await self._execute_sequential(
                batch_items, request, diagram_data, base_context
            )
        
        # Compile batch results
        batch_output = {
            'total_items': len(batch_items),
            'successful': len(results),
            'failed': len(errors),
            'results': [r.value if hasattr(r, 'value') else r for r in results],
            'errors': errors if errors else None
        }
        
        # Log batch completion
        log.debug(f"Batch execution completed: {len(results)} successful, {len(errors)} failed")
        
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
    
    def _extract_batch_items(self, inputs: Optional[dict[str, Any]], batch_input_key: str) -> list[Any]:
        """Extract batch items from inputs."""
        if not inputs:
            return []
        
        # Check if batch_input_key is in the root level or in 'default'
        if batch_input_key in inputs:
            batch_items = inputs.get(batch_input_key, [])
        elif 'default' in inputs and isinstance(inputs['default'], dict):
            batch_items = inputs['default'].get(batch_input_key, [])
        else:
            batch_items = []
        
        if not isinstance(batch_items, list):
            log.warning(f"Batch input '{batch_input_key}' is not a list. Treating as single item.")
            batch_items = [batch_items]
        
        return batch_items
    
    async def _prepare_base_context(self, request: ExecutionRequest[SubDiagramNode]) -> dict[str, Any]:
        """Prepare base execution context that will be reused for all batch items."""
        # Get required services
        state_store = request.services.resolve(STATE_STORE)
        message_router = request.services.resolve(MESSAGE_ROUTER)
        diagram_storage_service = request.services.resolve(DIAGRAM_STORAGE_SERVICE)
        
        if not all([state_store, message_router]):
            raise ValueError("Required services not available")
        
        # Get service registry and container
        service_registry = request.parent_registry
        if not service_registry:
            from dipeo.application.registry import ServiceRegistry, ServiceKey
            service_registry = ServiceRegistry()
            for service_name, service in request.services.items():
                key = ServiceKey(service_name)
                service_registry.register(key, service)
        
        container = request.parent_container
        
        return {
            'state_store': state_store,
            'message_router': message_router,
            'diagram_storage_service': diagram_storage_service,
            'service_registry': service_registry,
            'container': container,
            'parent_execution_id': request.execution_id
        }
    
    async def _execute_parallel(
        self,
        batch_items: list[Any],
        request: ExecutionRequest[SubDiagramNode],
        diagram_data: dict[str, Any],
        base_context: dict[str, Any],
        max_concurrent: int
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items in parallel with concurrency control."""
        results = []
        errors = []
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(item: Any, index: int) -> Any:
            """Execute single item with semaphore control."""
            async with semaphore:
                return await self._execute_single_item(
                    item, index, len(batch_items), request, diagram_data, base_context
                )
        
        # Create tasks for all items
        tasks = []
        for idx, item in enumerate(batch_items):
            task = execute_with_semaphore(item, idx)
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
        
        return results, errors
    
    async def _execute_sequential(
        self,
        batch_items: list[Any],
        request: ExecutionRequest[SubDiagramNode],
        diagram_data: dict[str, Any],
        base_context: dict[str, Any]
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items sequentially."""
        results = []
        errors = []
        
        for idx, item in enumerate(batch_items):
            try:
                result = await self._execute_single_item(
                    item, idx, len(batch_items), request, diagram_data, base_context
                )
                results.append(result)
            except Exception as e:
                log.error(f"Error processing batch item {idx}: {e}")
                errors.append({
                    'index': idx,
                    'error': str(e),
                    'item': item
                })
        
        return results, errors
    
    async def _execute_single_item(
        self,
        item: Any,
        index: int,
        total: int,
        original_request: ExecutionRequest[SubDiagramNode],
        diagram_data: dict[str, Any],
        base_context: dict[str, Any]
    ) -> Any:
        """Execute a single item in the batch with optimized context."""
        # Create lightweight execution context for this item
        item_inputs = {'default': item, '_batch_index': index}
        
        # Create a unique execution ID for this batch item
        sub_execution_id = f"{base_context['parent_execution_id']}_batch_{index}_{uuid.uuid4().hex[:8]}"
        
        # Prepare execution options
        options = {
            "variables": item_inputs,
            "parent_execution_id": base_context['parent_execution_id'],
            "is_sub_diagram": True,
            "is_batch_item": True,
            "batch_index": index,
            "batch_total": total,
            "metadata": {
                "is_sub_diagram": True,
                "is_batch_item": True,
                "parent_execution_id": base_context['parent_execution_id'],
                "batch_index": index,
                "batch_total": total
            }
        }
        
        # Create execution use case for this item
        execute_use_case = ExecuteDiagramUseCase(
            service_registry=base_context['service_registry'],
            state_store=base_context['state_store'],
            message_router=base_context['message_router'],
            diagram_storage_service=base_context['diagram_storage_service'],
            container=base_context['container']
        )
        
        # Execute with minimal observers for batch items
        parent_observers = []
        
        # Execute and collect only final results
        execution_results, execution_error = await self._execute_optimized(
            execute_use_case=execute_use_case,
            diagram_data=diagram_data,
            options=options,
            sub_execution_id=sub_execution_id,
            parent_observers=parent_observers
        )
        
        # Handle execution error
        if execution_error:
            raise Exception(f"Batch item {index} failed: {execution_error}")
        
        # Process output mapping
        output_value = self._process_output_mapping(original_request.node, execution_results)
        
        return DataOutput(
            value=output_value,
            node_id=f"{original_request.node.id}_batch_{index}",
            metadata={
                "batch_index": index,
                "sub_execution_id": sub_execution_id,
                "status": "completed"
            }
        )
    
    async def _execute_optimized(
        self,
        execute_use_case: "ExecuteDiagramUseCase",
        diagram_data: dict[str, Any],
        options: dict[str, Any],
        sub_execution_id: str,
        parent_observers: list[Any]
    ) -> tuple[dict[str, Any], Optional[str]]:
        """Execute sub-diagram with optimized update collection for batch processing."""
        execution_results = {}
        execution_error = None
        
        # Only collect essential updates for batch processing
        async for update in execute_use_case.execute_diagram(
            diagram=diagram_data,
            options=options,
            execution_id=sub_execution_id,
            interactive_handler=None,
            observers=parent_observers
        ):
            update_type = update.get("type", "")
            
            # Only process node completions and execution status
            if update_type == "NODE_STATUS_CHANGED":
                data = update.get("data", {})
                if data.get("status") == "COMPLETED":
                    node_id = data.get("node_id")
                    node_output = data.get("output")
                    if node_id and node_output:
                        execution_results[node_id] = node_output
            
            elif update_type == "EXECUTION_STATUS_CHANGED":
                data = update.get("data", {})
                if data.get("status") == "COMPLETED":
                    break
                elif data.get("status") == "FAILED":
                    execution_error = data.get("error")
                    if not execution_error:
                        # Try to get more context from the data
                        execution_error = f"Execution failed (node_id: {data.get('node_id', 'unknown')})"
                    break
            
            # Legacy support (minimal)
            elif update_type == "execution_complete":
                break
            elif update_type == "execution_error":
                execution_error = update.get("error")
                if not execution_error:
                    # If no error message provided, try to get status for more context
                    status = update.get("status", "unknown")
                    execution_error = f"Execution failed with status: {status}"
                break
        
        return execution_results, execution_error
    
    async def _get_diagram_input(self, node: SubDiagramNode, request: ExecutionRequest[SubDiagramNode]) -> Any:
        """Get the diagram input for preparation.
        
        Returns either diagram_data dict, a DomainDiagram, or a string ID/path.
        """
        # If diagram_data is provided directly, return it
        if node.diagram_data:
            return node.diagram_data
        
        # Otherwise, construct the diagram path/ID
        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")
        
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
        
        # Load the diagram using the diagram service if available
        diagram_service = request.services.resolve(DIAGRAM_SERVICE_NEW)
        
        if not diagram_service:
            # Return the path and let the prepare use case handle loading
            return file_path
        
        try:
            # Load the diagram - this returns a DomainDiagram
            diagram = await diagram_service.load_from_file(file_path)
            return diagram
        except Exception as e:
            log.error(f"Error loading diagram from '{file_path}': {str(e)}")
            # Return the path and let prepare use case try to load it
            return file_path
    
    async def _load_diagram_fallback(self, node: SubDiagramNode, diagram_service: Any) -> dict[str, Any]:
        """Fallback diagram loading (old implementation)."""
        # If diagram_data is provided directly, use it
        if node.diagram_data:
            return node.diagram_data
        
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
        if diagram_name.startswith('codegen/'):
            file_path = f"files/{diagram_name}{format_suffix}"
        else:
            file_path = f"files/diagrams/{diagram_name}{format_suffix}"
        
        try:
            # Use diagram service to load the diagram
            diagram = await diagram_service.load_from_file(file_path)
            return diagram
            
        except Exception as e:
            log.error(f"Error loading diagram from '{file_path}': {str(e)}")
            raise ValueError(f"Failed to load diagram '{node.diagram_name}': {str(e)}")
    
    def _process_output_mapping(self, node: SubDiagramNode, execution_results: dict[str, Any]) -> dict[str, Any]:
        """Process output mapping from sub-diagram results."""
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