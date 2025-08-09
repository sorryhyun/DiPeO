"""Batch person job executor - handles parallel execution of person jobs for batch operations."""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Optional
from dataclasses import replace

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.diagram_generated.generated_nodes import PersonJobNode
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.domain.conversation import Person

from .single_executor import SinglePersonJobExecutor

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BatchPersonJobExecutor:
    """Executor for batch person job execution with optimizations for parallel processing."""
    
    # Default configuration for batch execution
    DEFAULT_MAX_CONCURRENT = 10  # Maximum concurrent executions
    DEFAULT_BATCH_SIZE = 100     # Maximum items to process in one batch
    
    def __init__(self, person_cache: dict[str, Person]):
        """Initialize with shared person cache."""
        self._person_cache = person_cache
        self._single_executor = SinglePersonJobExecutor(person_cache)
    
    async def execute(self, request: ExecutionRequest[PersonJobNode]) -> NodeOutputProtocol:
        """Execute person job for each item in the batch."""
        node = request.node
        
        # Get batch configuration
        batch_input_key = getattr(node, 'batch_input_key', 'items')
        batch_parallel = getattr(node, 'batch_parallel', True)
        max_concurrent = getattr(node, 'max_concurrent', self.DEFAULT_MAX_CONCURRENT)
        
        logger.debug(f"Batch configuration - key: {batch_input_key}, parallel: {batch_parallel}, max_concurrent: {max_concurrent}")
        logger.debug(f"Request inputs: {request.inputs}")
        
        # Extract array from inputs
        batch_items = self._extract_batch_items(request.inputs, batch_input_key)
        
        if not batch_items:
            logger.warning(f"Batch mode enabled but no items found for key '{batch_input_key}'")
            return DataOutput(
                value={'total_items': 0, 'successful': 0, 'failed': 0, 'results': [], 'errors': None},
                node_id=node.id,
                metadata={'batch_mode': True, 'batch_parallel': batch_parallel, 'status': 'completed'}
            )
        
        logger.info(f"Processing batch of {len(batch_items)} items for person {node.person}")
        
        # Execute batch items
        if batch_parallel:
            results, errors = await self._execute_parallel(
                batch_items, request, max_concurrent
            )
        else:
            results, errors = await self._execute_sequential(
                batch_items, request
            )
        
        # Compile batch results
        batch_output = {
            'total_items': len(batch_items),
            'successful': len(results),
            'failed': len(errors),
            'results': results,
            'errors': errors if errors else None
        }
        
        # Return batch output
        return DataOutput(
            value=batch_output,
            node_id=node.id,
            metadata={
                'batch_mode': True,
                'batch_parallel': batch_parallel,
                'status': 'completed' if not errors else 'partial_failure',
                'person': node.person
            }
        )
    
    def _extract_batch_items(self, inputs: Optional[dict[str, Any]], batch_input_key: str) -> list[Any]:
        """Extract batch items from inputs."""
        if not inputs:
            return []
        
        logger.debug(f"Extracting batch items with key '{batch_input_key}' from inputs: {list(inputs.keys())}")
        
        # Check multiple possible locations for batch items
        batch_items = None
        
        # 1. Direct key in inputs
        if batch_input_key in inputs:
            batch_items = inputs.get(batch_input_key, [])
            logger.debug(f"Found batch items at root level: {type(batch_items)}")
        
        # 2. Under 'default' key
        elif 'default' in inputs:
            if isinstance(inputs['default'], dict) and batch_input_key in inputs['default']:
                batch_items = inputs['default'].get(batch_input_key, [])
                logger.debug(f"Found batch items under 'default': {type(batch_items)}")
            elif batch_input_key == 'default':
                # The batch items ARE the default value
                batch_items = inputs['default']
                logger.debug(f"Batch items are the default value itself: {type(batch_items)}")
        
        # 3. Under nested structure from Start node's custom_data
        elif 'default' in inputs and isinstance(inputs['default'], dict):
            # Check if the entire default dict has our key
            for key, value in inputs['default'].items():
                if key == batch_input_key:
                    batch_items = value
                    logger.debug(f"Found batch items in default dict at key '{key}': {type(batch_items)}")
                    break
        
        if batch_items is None:
            batch_items = []
            logger.warning(f"No batch items found for key '{batch_input_key}'")
        
        if not isinstance(batch_items, list):
            logger.warning(f"Batch input '{batch_input_key}' is not a list (type: {type(batch_items)}). Treating as single item.")
            batch_items = [batch_items]
        
        return batch_items
    
    async def _execute_parallel(
        self,
        batch_items: list[Any],
        request: ExecutionRequest[PersonJobNode],
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
                    item, index, len(batch_items), request
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
                logger.error(f"Batch item {idx} failed with error: {result}")
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
        request: ExecutionRequest[PersonJobNode]
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """Execute batch items sequentially."""
        results = []
        errors = []
        
        for idx, item in enumerate(batch_items):
            try:
                result = await self._execute_single_item(
                    item, idx, len(batch_items), request
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing batch item {idx}: {e}", exc_info=True)
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
        original_request: ExecutionRequest[PersonJobNode]
    ) -> Any:
        """Execute a single item in the batch."""
        node = original_request.node
        
        # Create item-specific inputs
        item_inputs = {
            'default': item,
            '_batch_index': index,
            '_batch_total': total
        }
        
        # Merge with original inputs (excluding the batch array)
        batch_input_key = getattr(node, 'batch_input_key', 'items')
        if original_request.inputs:
            for key, value in original_request.inputs.items():
                if key != batch_input_key and key != 'default':
                    item_inputs[key] = value
        
        # Create a new request for this batch item
        item_request = ExecutionRequest(
            node=node,
            context=original_request.context,
            inputs=item_inputs,
            services=original_request.services,
            execution_id=f"{original_request.execution_id}_batch_{index}",
            metadata={
                **original_request.metadata,
                'batch_index': index,
                'batch_total': total,
                'is_batch_item': True
            },
            parent_registry=original_request.parent_registry,
            parent_container=original_request.parent_container
        )
        
        # Execute using single executor
        logger.debug(f"Executing batch item {index + 1}/{total} for person {node.person}")
        result = await self._single_executor.execute(item_request)
        
        # Extract the value from the output
        if hasattr(result, 'value'):
            return {
                'index': index,
                'output': result.value,
                'metadata': result.metadata if hasattr(result, 'metadata') else {}
            }
        else:
            return {
                'index': index,
                'output': str(result),
                'metadata': {}
            }