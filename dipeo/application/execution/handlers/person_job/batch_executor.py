"""Batch execution logic for PersonJob nodes."""

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.config.base_logger import get_module_logger
from dipeo.config.execution import BATCH_MAX_CONCURRENT, BATCH_SIZE
from dipeo.diagram_generated.unified_nodes.person_job_node import PersonJobNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

from .batch_helpers import (
    extract_batch_items,
    format_batch_error,
    format_item_result,
)

if TYPE_CHECKING:
    pass

logger = get_module_logger(__name__)


class BatchExecutor:
    """Handles batch execution for PersonJob nodes.

    This class encapsulates all batch-related execution logic,
    including parallel and sequential processing, error handling,
    and result aggregation.
    """

    DEFAULT_MAX_CONCURRENT = BATCH_MAX_CONCURRENT
    DEFAULT_BATCH_SIZE = BATCH_SIZE

    def __init__(self, execute_single_callback: Callable):
        """Initialize BatchExecutor with required dependencies.

        Args:
            execute_single_callback: Callback to execute a single PersonJob
        """
        self._execute_single = execute_single_callback

    async def execute_batch(self, request: ExecutionRequest[PersonJobNode]) -> Envelope:
        """Execute person job for each item in the batch.

        Args:
            request: Execution request containing node, context, and inputs

        Returns:
            Envelope containing batch execution results
        """
        node = request.node
        trace_id = request.execution_id or ""

        # Get batch configuration
        batch_config = self._get_batch_configuration(node)

        logger.debug(
            f"Batch configuration - key: {batch_config['input_key']}, "
            f"parallel: {batch_config['parallel']}, "
            f"max_concurrent: {batch_config['max_concurrent']}"
        )

        # Extract array from inputs
        batch_items = extract_batch_items(request.inputs, batch_config["input_key"])

        if not batch_items:
            return self._create_empty_batch_output(node, batch_config, trace_id)

        logger.info(f"Processing batch of {len(batch_items)} items for person {node.person}")

        # Execute batch items
        if batch_config["parallel"]:
            results, errors = await self._execute_batch_parallel(
                batch_items, request, batch_config["max_concurrent"]
            )
        else:
            results, errors = await self._execute_batch_sequential(batch_items, request)

        # Return batch output
        return self._create_batch_output(
            node=node,
            batch_items=batch_items,
            results=results,
            errors=errors,
            batch_config=batch_config,
            trace_id=trace_id,
        )

    def _get_batch_configuration(self, node: PersonJobNode) -> dict[str, Any]:
        """Extract batch configuration from node.

        Args:
            node: PersonJobNode containing batch configuration

        Returns:
            Dictionary with batch configuration settings
        """
        return {
            "input_key": getattr(node, "batch_input_key", "items"),
            "parallel": getattr(node, "batch_parallel", True),
            "max_concurrent": getattr(node, "max_concurrent", self.DEFAULT_MAX_CONCURRENT),
        }

    async def _execute_batch_parallel(
        self, batch_items: list[Any], request: ExecutionRequest[PersonJobNode], max_concurrent: int
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items in parallel with concurrency control.

        Args:
            batch_items: List of items to process
            request: Original execution request
            max_concurrent: Maximum concurrent executions

        Returns:
            Tuple of (results, errors)
        """
        results = []
        errors = []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(batch_item: Any, index: int) -> Any:
            async with semaphore:
                return await self._execute_batch_item(batch_item, index, len(batch_items), request)

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
                error = format_batch_error(idx, result, batch_items)
                logger.error(f"Batch item {idx} failed: {error['error']}")
                errors.append(error)
            else:
                results.append(result)

        return results, errors

    async def _execute_batch_sequential(
        self, batch_items: list[Any], request: ExecutionRequest[PersonJobNode]
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items sequentially.

        Args:
            batch_items: List of items to process
            request: Original execution request

        Returns:
            Tuple of (results, errors)
        """
        results = []
        errors = []

        for idx, item in enumerate(batch_items):
            try:
                result = await self._execute_batch_item(item, idx, len(batch_items), request)
                results.append(result)
            except Exception as e:
                error = format_batch_error(idx, e, batch_items)
                logger.error(f"Error processing batch item {idx}: {error['error']}", exc_info=True)
                errors.append(error)

        return results, errors

    async def _execute_batch_item(
        self, item: Any, index: int, total: int, original_request: ExecutionRequest[PersonJobNode]
    ) -> dict[str, Any]:
        """Execute a single item in the batch.

        Args:
            item: The batch item to process
            index: Index of the item in the batch
            total: Total number of items in the batch
            original_request: The original execution request

        Returns:
            Formatted result dictionary
        """
        node = original_request.node

        # Create item-specific inputs
        item_inputs = self._create_item_inputs(
            item=item, index=index, total=total, original_request=original_request
        )

        # Create a new request for this batch item
        item_request = self._create_item_request(
            node=node, item_inputs=item_inputs, index=index, original_request=original_request
        )

        # Execute using single execution logic
        logger.debug(f"Executing batch item {index + 1}/{total} for person {node.person}")
        result = await self._execute_single(item_request)

        # Format the result
        return format_item_result(index, result)

    def _create_item_inputs(
        self, item: Any, index: int, total: int, original_request: ExecutionRequest[PersonJobNode]
    ) -> dict[str, Any]:
        """Create inputs for a single batch item.

        Args:
            item: The batch item
            index: Index of the item
            total: Total number of items
            original_request: Original execution request

        Returns:
            Dictionary of inputs for the item
        """
        node = original_request.node
        batch_input_key = getattr(node, "batch_input_key", "items")

        item_inputs = {"default": item, "_batch_index": index, "_batch_total": total}

        # Merge with original inputs (excluding the batch array)
        if original_request.inputs:
            for key, value in original_request.inputs.items():
                if key != batch_input_key and key != "default":
                    item_inputs[key] = value

        return item_inputs

    def _create_item_request(
        self,
        node: PersonJobNode,
        item_inputs: dict[str, Any],
        index: int,
        original_request: ExecutionRequest[PersonJobNode],
    ) -> ExecutionRequest[PersonJobNode]:
        """Create an execution request for a single batch item.

        Args:
            node: The PersonJobNode
            item_inputs: Inputs for the item
            index: Index of the item
            original_request: Original execution request

        Returns:
            New ExecutionRequest for the batch item
        """
        return ExecutionRequest(
            node=node,
            context=original_request.context,
            inputs=item_inputs,
            services=original_request.services,
            execution_id=f"{original_request.execution_id}_batch_{index}",
            metadata={},
            parent_registry=original_request.parent_registry,
            parent_container=original_request.parent_container,
        )

    def _create_empty_batch_output(
        self, node: PersonJobNode, batch_config: dict[str, Any], trace_id: str = ""
    ) -> Envelope:
        """Create an Envelope for empty batch.

        Args:
            node: The PersonJobNode
            batch_config: Batch configuration
            trace_id: Execution trace ID

        Returns:
            Envelope with empty batch result
        """
        logger.warning(
            f"Batch mode enabled but no items found for key '{batch_config['input_key']}'"
        )

        empty_result = {
            "total_items": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
            "errors": None,
        }

        envelope = EnvelopeFactory.create(body=empty_result, produced_by=node.id, trace_id=trace_id)
        envelope = envelope.with_meta(
            batch_mode="empty", batch_parallel=batch_config["parallel"], person_id=node.person
        )

        return envelope

    def _create_batch_output(
        self,
        node: PersonJobNode,
        batch_items: list[Any],
        results: list[Any],
        errors: list[dict[str, Any]],
        batch_config: dict[str, Any],
        trace_id: str = "",
    ) -> Envelope:
        """Create an Envelope containing batch execution results.

        Args:
            node: The PersonJobNode
            batch_items: Original batch items
            results: Successful results
            errors: Error information
            batch_config: Batch configuration
            trace_id: Execution trace ID

        Returns:
            Envelope with batch execution results
        """
        batch_output = {
            "total_items": len(batch_items),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors if errors else None,
        }

        envelope = EnvelopeFactory.create(body=batch_output, produced_by=node.id, trace_id=trace_id)

        meta = {
            "batch_mode": "completed",
            "batch_parallel": batch_config["parallel"],
            "total_items": len(batch_items),
            "successful": len(results),
            "failed": len(errors),
            "person_id": node.person,
        }
        envelope = envelope.with_meta(**meta)

        return envelope
