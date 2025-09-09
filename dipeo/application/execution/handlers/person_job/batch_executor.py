"""Batch person job executor - handles parallel execution of person jobs for batch operations."""

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.config.execution import BATCH_MAX_CONCURRENT, BATCH_SIZE
from dipeo.diagram_generated.unified_nodes.person_job_node import PersonJobNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

from .single_executor import SinglePersonJobExecutor

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BatchPersonJobExecutor:
    """Executor for batch person job execution with optimizations for parallel processing."""

    # Default configuration for batch execution
    DEFAULT_MAX_CONCURRENT = BATCH_MAX_CONCURRENT  # Maximum concurrent executions
    DEFAULT_BATCH_SIZE = BATCH_SIZE  # Maximum items to process in one batch

    def __init__(self):
        """Initialize the batch executor."""
        self._single_executor = SinglePersonJobExecutor()

    def _get_batch_configuration(self, node: PersonJobNode) -> dict[str, Any]:
        """Extract batch configuration from node."""
        return {
            "input_key": getattr(node, "batch_input_key", "items"),
            "parallel": getattr(node, "batch_parallel", True),
            "max_concurrent": getattr(node, "max_concurrent", self.DEFAULT_MAX_CONCURRENT),
        }

    def _create_empty_batch_output(
        self, node: PersonJobNode, batch_config: dict[str, Any], trace_id: str = ""
    ) -> Envelope:
        """Create an Envelope for empty batch with multi-representation."""
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

        # Build representations for empty batch
        representations = {
            "text": "No items to process (empty batch)",
            "object": empty_result,
            "summary": {"total_items": 0, "successful": 0, "failed": 0, "success_rate": "N/A"},
            "outputs": [],
            "detailed_results": [],
            "errors": [],
        }

        # Create envelope with representations
        envelope = EnvelopeFactory.create(body=empty_result, produced_by=node.id, trace_id=trace_id)

        # Representations no longer needed - removed deprecated with_representations() call

        # Add metadata
        envelope = envelope.with_meta(
            batch_mode="empty", batch_parallel=batch_config["parallel"], person_id=node.person
        )

        return envelope

    async def _execute_batch(
        self,
        batch_items: list[Any],
        request: ExecutionRequest[PersonJobNode],
        batch_config: dict[str, Any],
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items based on configuration."""
        if batch_config["parallel"]:
            return await self._execute_parallel(
                batch_items, request, batch_config["max_concurrent"]
            )
        else:
            return await self._execute_sequential(batch_items, request)

    def _build_batch_output(
        self,
        batch_items: list[Any],
        results: list[Any],
        errors: list[dict[str, Any]],
        batch_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Build multi-representation output for batch execution."""
        batch_output = {
            "total_items": len(batch_items),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors if errors else None,
        }

        # Build text representation
        text_parts = [f"Processed {len(batch_items)} items"]
        if results:
            text_parts.append(f"{len(results)} successful")
        if errors:
            text_parts.append(f"{len(errors)} failed")
        text_representation = ", ".join(text_parts)

        # Extract just the outputs from results for a cleaner view
        outputs_only = [r.get("output") for r in results if "output" in r]

        # Build representations
        representations = {
            "text": text_representation,
            "object": batch_output,
            "summary": {
                "total_items": len(batch_items),
                "successful": len(results),
                "failed": len(errors),
                "success_rate": f"{(len(results) / len(batch_items) * 100):.1f}%"
                if batch_items
                else "N/A",
            },
            "outputs": outputs_only,
            "detailed_results": results,
            "errors": errors if errors else [],
        }

        return {
            "primary": batch_output,
            "representations": representations,
            "meta": {
                "batch_mode": "completed",
                "batch_parallel": batch_config["parallel"],
                "total_items": len(batch_items),
                "successful": len(results),
                "failed": len(errors),
            },
        }

    def _create_batch_output(
        self,
        node: PersonJobNode,
        batch_items: list[Any],
        results: list[Any],
        errors: list[dict[str, Any]],
        batch_config: dict[str, Any],
        trace_id: str = "",
    ) -> Envelope:
        """Create an Envelope containing batch execution results with multi-representation."""
        # Build multi-representation output
        output = self._build_batch_output(batch_items, results, errors, batch_config)

        # Create envelope with primary body for backward compatibility
        envelope = EnvelopeFactory.create(
            body=output["primary"], produced_by=node.id, trace_id=trace_id
        )

        # Representations no longer needed - removed deprecated with_representations() call

        # Add metadata including person_id
        meta = output.get("meta", {})
        meta["person_id"] = node.person
        envelope = envelope.with_meta(**meta)

        return envelope

    async def execute(self, request: ExecutionRequest[PersonJobNode]) -> Envelope:
        """Execute person job for each item in the batch and return an Envelope."""
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
        batch_items = self._extract_batch_items(request.inputs, batch_config["input_key"])

        if not batch_items:
            return self._create_empty_batch_output(node, batch_config, trace_id)

        logger.info(f"Processing batch of {len(batch_items)} items for person {node.person}")

        # Execute batch items
        results, errors = await self._execute_batch(batch_items, request, batch_config)

        # Return batch output with envelope
        return self._create_batch_output(
            node=node,
            batch_items=batch_items,
            results=results,
            errors=errors,
            batch_config=batch_config,
            trace_id=trace_id,
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

        logger.debug(
            f"Extracting batch items with key '{batch_input_key}' from inputs: {list(inputs.keys())}"
        )

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
                logger.debug("Found batch items under 'default'")
                return default_value[batch_input_key]

            # Check if the batch items ARE the default value
            if batch_input_key == "default":
                logger.debug("Batch items are the default value itself")
                return default_value

            # Search nested structure
            if isinstance(default_value, dict):
                for key, value in default_value.items():
                    if key == batch_input_key:
                        logger.debug(f"Found batch items in default dict at key '{key}'")
                        return value

        return None

    async def _execute_parallel(
        self, batch_items: list[Any], request: ExecutionRequest[PersonJobNode], max_concurrent: int
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items in parallel with concurrency control."""
        results = []
        errors = []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(batch_item: Any, index: int) -> Any:
            """Execute single item with semaphore control."""
            async with semaphore:
                return await self._execute_single_item(batch_item, index, len(batch_items), request)

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
        self, batch_items: list[Any], request: ExecutionRequest[PersonJobNode]
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items sequentially."""
        results = []
        errors = []

        for idx, item in enumerate(batch_items):
            try:
                result = await self._execute_single_item(item, idx, len(batch_items), request)
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
        self, item: Any, index: int, total: int, original_request: ExecutionRequest[PersonJobNode]
    ) -> dict[str, Any]:
        """Execute a single item in the batch."""
        node = original_request.node

        # Create item-specific inputs
        item_inputs = self._create_item_inputs(
            item=item, index=index, total=total, original_request=original_request
        )

        # Create a new request for this batch item
        item_request = self._create_item_request(
            node=node, item_inputs=item_inputs, index=index, original_request=original_request
        )

        # Execute using single executor
        logger.debug(f"Executing batch item {index + 1}/{total} for person {node.person}")
        result = await self._single_executor.execute(item_request)

        # Format the result
        return self._format_item_result(index, result)

    def _create_item_inputs(
        self, item: Any, index: int, total: int, original_request: ExecutionRequest[PersonJobNode]
    ) -> dict[str, Any]:
        """Create inputs for a single batch item."""
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
        """Create an execution request for a single batch item."""
        return ExecutionRequest(
            node=node,
            context=original_request.context,
            inputs=item_inputs,
            services=original_request.services,
            execution_id=f"{original_request.execution_id}_batch_{index}",
            metadata={},  # Clean metadata - no propagation
            parent_registry=original_request.parent_registry,
            parent_container=original_request.parent_container,
        )

    def _format_item_result(self, index: int, result: Any) -> dict[str, Any]:
        """Format the result from a single item execution."""
        # Handle Envelope result from single_executor
        if hasattr(result, "body"):  # It's an Envelope
            output_value = result.body
            # Extract metadata from envelope's meta field
            metadata = result.meta if hasattr(result, "meta") else {}

            return {"index": index, "output": output_value, "metadata": metadata}
        else:
            # Fallback for unexpected format
            return {"index": index, "output": str(result), "metadata": {}}
