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

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
from dipeo.config.base_logger import get_module_logger
from dipeo.config.execution import SUB_DIAGRAM_BATCH_SIZE, SUB_DIAGRAM_MAX_CONCURRENT
from dipeo.diagram_generated import Status
from dipeo.diagram_generated.unified_nodes.sub_diagram_node import SubDiagramNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

from .base_executor import BaseSubDiagramExecutor

if TYPE_CHECKING:
    pass

logger = get_module_logger(__name__)


class BatchSubDiagramExecutor(BaseSubDiagramExecutor):
    """Executor for batch sub-diagram execution with optimizations for parallel processing."""

    DEFAULT_MAX_CONCURRENT = SUB_DIAGRAM_MAX_CONCURRENT
    DEFAULT_BATCH_SIZE = SUB_DIAGRAM_BATCH_SIZE

    def __init__(self):
        super().__init__()

    def set_services(self, state_store, message_router, diagram_service, service_registry=None):
        super().set_services(
            state_store=state_store,
            message_router=message_router,
            diagram_service=diagram_service,
            service_registry=service_registry,
        )

    def _get_batch_configuration(self, node: SubDiagramNode) -> dict[str, Any]:
        return {
            "input_key": getattr(node, "batch_input_key", "items"),
            "parallel": getattr(node, "batch_parallel", True),
            "max_concurrent": getattr(node, "max_concurrent", self.DEFAULT_MAX_CONCURRENT),
        }

    def _create_empty_batch_output(
        self, node: SubDiagramNode, batch_config: dict[str, Any]
    ) -> Envelope:
        logger.warning(
            f"Batch mode enabled but no items found for key '{batch_config['input_key']}'"
        )
        return EnvelopeFactory.create(
            body={"total_items": 0, "successful": 0, "failed": 0, "results": [], "errors": None},
            produced_by=str(node.id),
            meta={"batch_parallel": batch_config["parallel"]},
        )

    async def execute(self, request: ExecutionRequest[SubDiagramNode]) -> Envelope:
        node = request.node

        batch_config = self._get_batch_configuration(node)

        batch_items = self._extract_batch_items(request.inputs, batch_config["input_key"])

        if not batch_items:
            return self._create_empty_batch_output(node, batch_config)

        domain_diagram = await self._load_diagram(node)

        base_context = await self._prepare_base_context(request)

        results, errors = await self._execute_batch(
            batch_items=batch_items,
            request=request,
            domain_diagram=domain_diagram,
            base_context=base_context,
            batch_config=batch_config,
        )

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
        output_mode = getattr(node, "output_mode", "pure_list")

        materialized_results = [r.value if hasattr(r, "value") else r for r in results]

        # Support both pure_list and rich_object output modes (SEAC compliance)
        if output_mode == "pure_list":
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

        batch_items = self._find_batch_items_in_inputs(inputs, batch_input_key)

        if batch_items is None:
            logger.warning(f"No batch items found for key '{batch_input_key}'")
            return []

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
        if batch_input_key in inputs:
            return inputs[batch_input_key]

        if "default" in inputs:
            default_value = inputs["default"]

            if isinstance(default_value, dict) and batch_input_key in default_value:
                return default_value[batch_input_key]

            if batch_input_key == "default":
                return default_value

            if isinstance(default_value, dict):
                for key, value in default_value.items():
                    if key == batch_input_key:
                        return value

        return None

    async def _prepare_base_context(
        self, request: ExecutionRequest[SubDiagramNode]
    ) -> dict[str, Any]:
        if not all([self._state_store, self._message_router, self._diagram_service]):
            raise ValueError("Required services not configured")

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

        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(batch_item: Any, index: int) -> Any:
            async with semaphore:
                return await self._execute_single_item(
                    batch_item, index, len(batch_items), request, domain_diagram, base_context
                )

        tasks = []
        for idx, item in enumerate(batch_items):
            task = execute_with_semaphore(item, idx)
            tasks.append(task)

        task_results = await asyncio.gather(*tasks, return_exceptions=True)

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
        domain_diagram: Any,
        base_context: dict[str, Any],
    ) -> dict[str, Any]:
        node = original_request.node

        item_inputs = self._create_item_inputs(
            item=item, index=index, total=total, original_request=original_request
        )

        sub_execution_id = self._create_sub_execution_id(
            parent_execution_id=base_context["parent_execution_id"], index=index
        )

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
                "parent_diagram": node.diagram_name or "inline",
                "batch_index": index,
                "batch_total": total,
                "diagram_scope": node.diagram_name,
            },
        }

        isolated_registry = self._create_isolated_registry(base_context["service_registry"])

        execute_use_case = ExecuteDiagramUseCase(
            service_registry=isolated_registry,
            state_store=base_context["state_store"],
            message_router=base_context["message_router"],
            diagram_service=base_context["diagram_service"],
            container=base_context["container"],
        )

        options["diagram_source_path"] = self._construct_diagram_path(node)

        execution_results, execution_error = await self._execute_optimized(
            execute_use_case=execute_use_case,
            domain_diagram=domain_diagram,
            options=options,
            sub_execution_id=sub_execution_id,
            event_filter=None,
        )

        if execution_error:
            raise Exception(f"Batch item {index} failed: {execution_error}")

        return self._format_item_result(index, node, sub_execution_id, execution_results)

    async def _execute_optimized(
        self,
        execute_use_case: "ExecuteDiagramUseCase",
        domain_diagram: Any,
        options: dict[str, Any],
        sub_execution_id: str,
        event_filter: Any | None,
    ) -> tuple[dict[str, Any], str | None]:
        """Execute sub-diagram with optimized update collection for batch processing."""
        execution_results = {}
        execution_error = None

        async for update in execute_use_case.execute_diagram(
            diagram=domain_diagram,
            options=options,
            execution_id=sub_execution_id,
            interactive_handler=None,
            event_filter=event_filter,
        ):
            update_type = update.get("type", "")

            if update_type == "NODE_STATUS_CHANGED":
                data = update.get("data", {})
                if data.get("status") == Status.COMPLETED:
                    node_id = data.get("node_id")
                    node_output = data.get("output")
                    if node_id and node_output:
                        if hasattr(node_output, "value"):
                            execution_results[node_id] = node_output.value
                        else:
                            execution_results[node_id] = node_output

            elif update_type in ["EXECUTION_COMPLETED", "execution_completed"]:
                break
            elif update_type in ["EXECUTION_ERROR", "execution_error"]:
                data = update.get("data", {})
                execution_error = data.get("error")
                if not execution_error:
                    execution_error = (
                        f"Execution failed (node_id: {data.get('node_id', 'unknown')})"
                    )
                break

            elif update_type == "execution_complete":
                break
            elif update_type == "execution_error":
                execution_error = update.get("error")
                if not execution_error:
                    status = update.get("status", "unknown")
                    execution_error = f"Execution failed with status: {status}"
                break

        return execution_results, execution_error

    def _create_item_inputs(
        self, item: Any, index: int, total: int, original_request: ExecutionRequest[SubDiagramNode]
    ) -> dict[str, Any]:
        node = original_request.node
        batch_input_key = getattr(node, "batch_input_key", "items")

        # Avoid double-wrapping when batch_input_key is 'default'
        if batch_input_key == "default":
            item_inputs = {
                **item,
                "_batch_index": index,
                "_batch_total": total,
            }
        else:
            item_inputs = {"default": item, "_batch_index": index, "_batch_total": total}

        if original_request.inputs:
            for key, value in original_request.inputs.items():
                if key != batch_input_key and key != "default":
                    item_inputs[key] = value

        return item_inputs

    def _create_sub_execution_id(self, parent_execution_id: str, index: int) -> str:
        return self._create_execution_id(parent_execution_id, f"batch_{index}")

    def _format_item_result(
        self,
        index: int,
        node: SubDiagramNode,
        sub_execution_id: str,
        execution_results: dict[str, Any],
    ) -> dict[str, Any]:
        output_value = self._process_output_mapping(node, execution_results)

        return {
            "index": index,
            "output": output_value,
            "metadata": {"sub_execution_id": sub_execution_id},
        }

    def _create_isolated_registry(self, parent_registry):
        """Create an isolated service registry for batch item execution.

        Copies parent registry to prevent state contamination between parallel executions.
        """
        from dipeo.application.registry import ServiceRegistry

        isolated_registry = ServiceRegistry()

        if hasattr(parent_registry, "_services"):
            for key_str, service in parent_registry._services.items():
                isolated_registry._services[key_str] = service

        return isolated_registry
