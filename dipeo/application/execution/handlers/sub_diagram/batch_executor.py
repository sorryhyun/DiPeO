"""Batch sub-diagram executor - handles parallel execution of sub-diagrams for batch operations.

This executor implements optimizations for batch parallel execution:
1. Loads diagram once and reuses for all batch items
2. Creates lightweight execution contexts
3. Uses fire-and-forget pattern for update collection
4. Focuses on collecting only final results
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
from dipeo.diagram_generated import Status
from dipeo.diagram_generated.unified_nodes.sub_diagram_node import SubDiagramNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

from .base_executor import BaseSubDiagramExecutor

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BatchSubDiagramExecutor(BaseSubDiagramExecutor):
    """Executor for batch sub-diagram execution with optimizations for parallel processing."""

    # Default configuration for batch execution
    DEFAULT_MAX_CONCURRENT = 10  # Maximum concurrent executions
    DEFAULT_BATCH_SIZE = 100  # Maximum items to process in one batch

    def __init__(self):
        """Initialize executor."""
        super().__init__()

    def set_services(self, state_store, message_router, diagram_service, service_registry=None):
        """Set services for the executor to use."""
        super().set_services(
            state_store=state_store,
            message_router=message_router,
            diagram_service=diagram_service,
            service_registry=service_registry,
        )

    def _get_batch_configuration(self, node: SubDiagramNode) -> dict[str, Any]:
        """Extract batch configuration from node."""
        return {
            "input_key": getattr(node, "batch_input_key", "items"),
            "parallel": getattr(node, "batch_parallel", True),
            "max_concurrent": getattr(node, "max_concurrent", self.DEFAULT_MAX_CONCURRENT),
        }

    def _create_empty_batch_output(
        self, node: SubDiagramNode, batch_config: dict[str, Any]
    ) -> Envelope:
        """Create output for empty batch."""
        logger.warning(
            f"Batch mode enabled but no items found for key '{batch_config['input_key']}'"
        )
        return EnvelopeFactory.create(
            body={"total_items": 0, "successful": 0, "failed": 0, "results": [], "errors": None},
            produced_by=str(node.id),
            meta={"batch_parallel": batch_config["parallel"]},
        )

    async def execute(self, request: ExecutionRequest[SubDiagramNode]) -> Envelope:
        """Execute sub-diagram for each item in the batch."""
        node = request.node

        # Get batch configuration
        batch_config = self._get_batch_configuration(node)

        # Extract array from inputs
        batch_items = self._extract_batch_items(request.inputs, batch_config["input_key"])

        if not batch_items:
            return self._create_empty_batch_output(node, batch_config)

        # Load and prepare diagram once for all batch items
        domain_diagram = await self._load_diagram(node)

        # Prepare base execution context
        base_context = await self._prepare_base_context(request)

        # Execute batch items based on configuration
        results, errors = await self._execute_batch(
            batch_items=batch_items,
            request=request,
            domain_diagram=domain_diagram,
            base_context=base_context,
            batch_config=batch_config,
        )

        # Return batch output
        return self._create_batch_output(
            node=node,
            batch_items=batch_items,
            results=results,
            errors=errors,
            batch_config=batch_config,
        )

    async def _execute_batch(
        self,
        batch_items: list[Any],
        request: ExecutionRequest[SubDiagramNode],
        domain_diagram: Any,
        base_context: dict[str, Any],
        batch_config: dict[str, Any],
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items based on configuration."""
        if batch_config["parallel"]:
            return await self._execute_parallel(
                batch_items, request, domain_diagram, base_context, batch_config["max_concurrent"]
            )
        else:
            return await self._execute_sequential(
                batch_items, request, domain_diagram, base_context
            )

    def _create_batch_output(
        self,
        node: SubDiagramNode,
        batch_items: list[Any],
        results: list[Any],
        errors: list[dict[str, Any]],
        batch_config: dict[str, Any],
    ) -> Envelope:
        """Create batch execution output based on output_mode setting."""
        # Get output mode from node properties, defaulting to pure_list for SEAC compliance
        output_mode = getattr(node, "output_mode", "pure_list")

        # Process results to extract values
        materialized_results = [r.value if hasattr(r, "value") else r for r in results]

        # SEAC: Support both pure_list and rich_object output modes
        if output_mode == "pure_list":
            # Pure list mode: envelope body is just the array
            return EnvelopeFactory.create(
                body=materialized_results,
                produced_by=str(node.id),
                meta={
                    "total_items": len(batch_items),
                    "successful": len(results),
                    "failed": len(errors),
                    "batch_parallel": batch_config["parallel"],
                    "diagram": node.diagram_name or "inline",
                    "errors": errors if errors else None,
                },
            )
        else:
            # Rich object mode: legacy wrapped output
            result_key = getattr(node, "result_key", "results")
            batch_output = {
                "total_items": len(batch_items),
                "successful": len(results),
                "failed": len(errors),
                result_key: materialized_results,
                "errors": errors if errors else None,
            }

            return EnvelopeFactory.create(
                body=batch_output,
                produced_by=str(node.id),
                meta={
                    "batch_parallel": batch_config["parallel"],
                    "diagram": node.diagram_name or "inline",
                },
            )

    def _extract_batch_items(
        self, inputs: dict[str, Any] | None, batch_input_key: str
    ) -> list[Any]:
        """Extract batch items from inputs.

        Searches for batch items in the following order:
        1. Direct key in inputs
        2. Under 'default' key
        3. Nested structure from Start node's custom_data
        """
        if not inputs:
            return []

        # Add detailed logging to debug the issue
        if "default" in inputs:
            default_value = inputs["default"]
            logger.debug(f"Type of 'default' value: {type(default_value)}")
            if isinstance(default_value, dict):
                logger.debug(f"Keys in 'default' dict: {list(default_value.keys())}")
            elif isinstance(default_value, str):
                logger.debug(f"'default' is a string, first 100 chars: {default_value[:100]}")

        batch_items = self._find_batch_items_in_inputs(inputs, batch_input_key)

        if batch_items is None:
            logger.warning(f"No batch items found for key '{batch_input_key}'")
            return []

        # Ensure batch_items is a list
        if not isinstance(batch_items, list):
            logger.warning(
                f"Batch input '{batch_input_key}' is not a list (type: {type(batch_items)}). "
                f"Treating as single item."
            )
            return [batch_items]

        return batch_items

    def _find_batch_items_in_inputs(
        self, inputs: dict[str, Any], batch_input_key: str
    ) -> Any | None:
        """Find batch items in various input structures."""
        # 1. Direct key in inputs
        if batch_input_key in inputs:
            logger.debug("Found batch items at root level")
            return inputs[batch_input_key]

        # 2. Under 'default' key
        if "default" in inputs:
            default_value = inputs["default"]

            # Check if default contains the key
            if isinstance(default_value, dict) and batch_input_key in default_value:
                return default_value[batch_input_key]

            # Check if the batch items ARE the default value
            if batch_input_key == "default":
                return default_value

            # Search nested structure
            if isinstance(default_value, dict):
                for key, value in default_value.items():
                    if key == batch_input_key:
                        return value

        return None

    async def _prepare_base_context(
        self, request: ExecutionRequest[SubDiagramNode]
    ) -> dict[str, Any]:
        """Prepare base execution context that will be reused for all batch items."""
        # Use pre-configured services
        if not all([self._state_store, self._message_router, self._diagram_service]):
            raise ValueError("Required services not configured")

        # Get service registry and container
        service_registry = request.parent_registry
        if not service_registry:
            from dipeo.application.registry import ServiceKey, ServiceRegistry

            service_registry = ServiceRegistry()
            for service_name, service in request.services.items():
                key = ServiceKey(service_name)
                service_registry.register(key, service)

        container = request.parent_container

        return {
            "state_store": self._state_store,
            "message_router": self._message_router,
            "diagram_service": self._diagram_service,
            "service_registry": service_registry,
            "container": container,
            "parent_execution_id": request.execution_id,
        }

    async def _execute_parallel(
        self,
        batch_items: list[Any],
        request: ExecutionRequest[SubDiagramNode],
        domain_diagram: Any,  # DomainDiagram
        base_context: dict[str, Any],
        max_concurrent: int,
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items in parallel with concurrency control."""
        results = []
        errors = []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(batch_item: Any, index: int) -> Any:
            """Execute single item with semaphore control."""
            async with semaphore:
                return await self._execute_single_item(
                    batch_item, index, len(batch_items), request, domain_diagram, base_context
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
                error = self._format_batch_error(idx, result, batch_items)
                logger.error(f"Batch item {idx} failed: {error['error']}")
                errors.append(error)
            else:
                results.append(result)

        return results, errors

    async def _execute_sequential(
        self,
        batch_items: list[Any],
        request: ExecutionRequest[SubDiagramNode],
        domain_diagram: Any,  # DomainDiagram
        base_context: dict[str, Any],
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items sequentially."""
        results = []
        errors = []

        for idx, item in enumerate(batch_items):
            try:
                result = await self._execute_single_item(
                    item, idx, len(batch_items), request, domain_diagram, base_context
                )
                results.append(result)
            except Exception as e:
                error = self._format_batch_error(idx, e, batch_items)
                logger.error(f"Error processing batch item {idx}: {error['error']}", exc_info=True)
                errors.append(error)

        return results, errors

    def _format_batch_error(
        self, index: int, error: Exception, batch_items: list[Any]
    ) -> dict[str, Any]:
        """Format error information for batch processing."""
        return {
            "index": index,
            "error": str(error),
            "error_type": type(error).__name__,
            "item": batch_items[index] if index < len(batch_items) else None,
        }

    async def _execute_single_item(
        self,
        item: Any,
        index: int,
        total: int,
        original_request: ExecutionRequest[SubDiagramNode],
        domain_diagram: Any,  # DomainDiagram
        base_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single item in the batch with optimized context."""
        node = original_request.node

        # Create item-specific inputs
        item_inputs = self._create_item_inputs(
            item=item, index=index, total=total, original_request=original_request
        )

        # Create a unique execution ID for this batch item
        sub_execution_id = self._create_sub_execution_id(
            parent_execution_id=base_context["parent_execution_id"], index=index
        )

        # Prepare execution options with proper parent diagram context
        options = {
            "variables": item_inputs,
            "parent_execution_id": base_context["parent_execution_id"],
            "is_sub_diagram": True,
            "is_batch_item": True,
            "batch_index": index,
            "batch_total": total,
            "metadata": {
                "is_sub_diagram": True,
                "is_batch_item": True,
                "parent_execution_id": base_context["parent_execution_id"],
                "parent_diagram": node.diagram_name or "inline",  # Fix: Add parent_diagram
                "batch_index": index,
                "batch_total": total,
                "diagram_scope": node.diagram_name,  # Add explicit scope
            },
        }

        # Create isolated context for this batch item to prevent cross-contamination
        isolated_registry = self._create_isolated_registry(base_context["service_registry"])

        # Create execution use case with isolated registry
        execute_use_case = ExecuteDiagramUseCase(
            service_registry=isolated_registry,
            state_store=base_context["state_store"],
            message_router=base_context["message_router"],
            diagram_service=base_context["diagram_service"],
            container=base_context["container"],
        )

        # Execute and collect only final results
        # Pass the diagram name in options to help with scoping
        options["diagram_source_path"] = self._construct_diagram_path(node)

        execution_results, execution_error = await self._execute_optimized(
            execute_use_case=execute_use_case,
            domain_diagram=domain_diagram,
            options=options,
            sub_execution_id=sub_execution_id,
            event_filter=None,  # No filtering needed for batch items
        )

        # Handle execution error
        if execution_error:
            raise Exception(f"Batch item {index} failed: {execution_error}")

        # Format the result
        return self._format_item_result(index, node, sub_execution_id, execution_results)

    async def _execute_optimized(
        self,
        execute_use_case: "ExecuteDiagramUseCase",
        domain_diagram: Any,  # DomainDiagram
        options: dict[str, Any],
        sub_execution_id: str,
        event_filter: Any | None,
    ) -> tuple[dict[str, Any], str | None]:
        """Execute sub-diagram with optimized update collection for batch processing."""
        execution_results = {}
        execution_error = None

        # Only collect essential updates for batch processing
        async for update in execute_use_case.execute_diagram(
            diagram=domain_diagram,
            options=options,
            execution_id=sub_execution_id,
            interactive_handler=None,
            event_filter=event_filter,
        ):
            update_type = update.get("type", "")

            # Only process node completions and execution status
            if update_type == "NODE_STATUS_CHANGED":
                data = update.get("data", {})
                if data.get("status") == Status.COMPLETED.value:
                    node_id = data.get("node_id")
                    node_output = data.get("output")
                    if node_id and node_output:
                        # Extract value from Envelope if present
                        if hasattr(node_output, "value"):
                            execution_results[node_id] = node_output.value
                        else:
                            execution_results[node_id] = node_output

            elif update_type == "EXECUTION_STATUS_CHANGED":
                data = update.get("data", {})
                if data.get("status") == Status.COMPLETED.value:
                    break
                elif data.get("status") == Status.FAILED.value:
                    execution_error = data.get("error")
                    if not execution_error:
                        # Try to get more context from the data
                        execution_error = (
                            f"Execution failed (node_id: {data.get('node_id', 'unknown')})"
                        )
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

    def _create_item_inputs(
        self, item: Any, index: int, total: int, original_request: ExecutionRequest[SubDiagramNode]
    ) -> dict[str, Any]:
        """Create inputs for a single batch item."""
        node = original_request.node
        batch_input_key = getattr(node, "batch_input_key", "items")

        # When batch_input_key is 'default', the item itself becomes the default input
        # to avoid double-wrapping when Start node processes it
        if batch_input_key == "default":
            # Don't wrap with 'default' key - let the item be the direct input
            item_inputs = {
                **item,  # Spread the item directly
                "_batch_index": index,
                "_batch_total": total,
            }
        else:
            # For other batch_input_keys, wrap with 'default' as before
            item_inputs = {"default": item, "_batch_index": index, "_batch_total": total}

        # Merge with original inputs (excluding the batch array)
        if original_request.inputs:
            for key, value in original_request.inputs.items():
                if key != batch_input_key and key != "default":
                    item_inputs[key] = value

        return item_inputs

    def _create_sub_execution_id(self, parent_execution_id: str, index: int) -> str:
        """Create a unique execution ID for batch item."""
        return self._create_execution_id(parent_execution_id, f"batch_{index}")

    def _format_item_result(
        self,
        index: int,
        node: SubDiagramNode,
        sub_execution_id: str,
        execution_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Format the result from a single item execution."""
        # Process output mapping
        output_value = self._process_output_mapping(node, execution_results)

        return {
            "index": index,
            "output": output_value,
            "metadata": {"sub_execution_id": sub_execution_id},
        }

    def _create_isolated_registry(self, parent_registry):
        """Create an isolated service registry for batch item execution.

        This creates a copy of the parent registry to prevent state contamination
        between parallel batch item executions.
        """
        from dipeo.application.registry import ServiceRegistry

        # Create new registry instance
        isolated_registry = ServiceRegistry()

        # Copy services from parent registry if possible
        if hasattr(parent_registry, "_services"):
            # Copy the services to ensure isolation
            # The registry stores keys as strings internally
            for key_str, service in parent_registry._services.items():
                # Directly assign to internal dict since keys are already strings
                isolated_registry._services[key_str] = service

        return isolated_registry
