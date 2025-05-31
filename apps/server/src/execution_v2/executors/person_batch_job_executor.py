"""PersonBatchJob node executor for batch LLM agent interactions."""

from typing import Any, Dict, Tuple, Optional, List
import asyncio
import logging

from .base_executor import BaseExecutor
from ..core.execution_context import ExecutionContext
from ..core.skip_manager import SkipManager
from ...utils.resolve_utils import render_prompt

logger = logging.getLogger(__name__)


class PersonBatchJobExecutor(BaseExecutor):
    """Executor for PersonBatchJob nodes - handles batch processing with LLM agents."""
    
    def __init__(self, context: ExecutionContext, llm_service=None, memory_service=None):
        """Initialize the person batch job executor."""
        super().__init__(context, llm_service, memory_service)
    
    async def validate_inputs(
        self,
        node: Dict[str, Any],
        context: ExecutionContext
    ) -> Optional[str]:
        """Validate PersonBatchJob node inputs.
        
        Args:
            node: The node configuration
            context: The execution context
            
        Returns:
            Error message if validation fails, None if valid
        """
        data = node.get('data', {})
        
        if not data.get('personId'):
            return "PersonBatchJob requires 'personId'"
        
        if not data.get('prompt'):
            return "PersonBatchJob requires 'prompt'"
        
        # Note: Person validation could be added here if diagram context is available
        return None
    
    async def execute(
        self,
        node: Dict[str, Any],
        context: ExecutionContext,
        skip_manager: SkipManager,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a PersonBatchJob node.
        
        Args:
            node: The node configuration
            context: The execution context
            skip_manager: The skip manager (not used here)
            **kwargs: Additional arguments
            
        Returns:
            Tuple of (aggregated_results, total_cost)
        """
        data = node.get('data', {})
        person_id = data['personId']
        prompt_template = data.get('prompt', '')
        batch_size = data.get('batchSize', 5)
        parallel = data.get('parallel', False)
        
        # Get person configuration from diagram context
        person = self._get_person_from_context(person_id, context)
        if not person:
            # Fallback to basic person config from node data if not found in context
            person = {
                'id': person_id,
                'service': data.get('service', 'openai'),
                'model': data.get('model', 'gpt-3.5-turbo'),
                'temperature': data.get('temperature', 0.7),
                'apiKey': data.get('apiKey')
            }
        
        # Prepare inputs
        inputs = self._prepare_inputs(node, context)
        
        # Convert inputs dict to list format
        input_list = []
        for key, value in inputs.items():
            if value is not None:
                input_list.append(value)
        
        if not input_list:
            logger.warning(f"PersonBatchJob {node['id']} has no inputs to process")
            return [], 0.0
        
        # Create vars_map
        vars_map = {}
        for node_id, output in context.node_outputs.items():
            vars_map[node_id] = output
        
        # Process in batches
        results = []
        total_cost = 0.0
        
        for i in range(0, len(input_list), batch_size):
            batch = input_list[i:i + batch_size]
            
            if parallel:
                # Process batch items in parallel
                batch_results = await self._process_batch_parallel(
                    batch, person, prompt_template, vars_map
                )
            else:
                # Process batch items sequentially
                batch_results = await self._process_batch_sequential(
                    batch, person, prompt_template, vars_map
                )
            
            for result, cost in batch_results:
                results.append(result)
                total_cost += cost
        
        # Aggregate results if configured
        aggregated = self._aggregate_results(results, data)
        
        return aggregated, total_cost
    
    async def _process_batch_parallel(
        self, batch: List[Any], person: dict, prompt_template: str, vars_map: dict
    ) -> List[Tuple[Any, float]]:
        """Process batch items in parallel."""
        tasks = []
        for item in batch:
            task = self._process_single_item(item, person, prompt_template, vars_map)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def _process_batch_sequential(
        self, batch: List[Any], person: dict, prompt_template: str, vars_map: dict
    ) -> List[Tuple[Any, float]]:
        """Process batch items sequentially."""
        results = []
        for item in batch:
            result = await self._process_single_item(item, person, prompt_template, vars_map)
            results.append(result)
        return results
    
    async def _process_single_item(
        self, item: Any, person: dict, prompt_template: str, vars_map: dict
    ) -> Tuple[Any, float]:
        """Process a single item in the batch."""
        # Add current item to vars_map
        item_vars = vars_map.copy()
        item_vars['_item'] = item
        item_vars['_index'] = getattr(item, '_index', 0)  # If item has index
        
        # Render prompt with item context
        rendered_prompt = render_prompt(prompt_template, item_vars)
        
        # Add item to prompt if it's not already included
        if '_item' not in prompt_template and str(item) not in rendered_prompt:
            rendered_prompt = f"{rendered_prompt}\n\nCurrent item:\n{item}"
        
        # Get conversation history if memory service is available
        conversation = []
        if self.memory_service:
            conversation = self.memory_service.get_conversation_history(person['id'])
            self.memory_service.add_message(person['id'], 'user', rendered_prompt)
        
        # Prepare messages for LLM
        messages = conversation + [{'role': 'user', 'content': rendered_prompt}]
        
        # Call LLM
        try:
            result = await self.llm_service.call_llm(
                messages=messages,
                service=person.get('service', 'openai'),
                model=person.get('model'),
                temperature=person.get('temperature', 0.7),
                api_key_id=person.get('apiKey')
            )
            
            response = result.get('response', '')
            cost = result.get('cost', 0.0)
            
            # Add assistant response to memory if available
            if self.memory_service:
                self.memory_service.add_message(person['id'], 'assistant', response)
            
            return response, cost
            
        except Exception as e:
            logger.error(f"Failed to process batch item: {e}")
            return None, 0.0
    
    def _get_person_from_context(self, person_id: str, context: ExecutionContext) -> Optional[dict]:
        """Get person configuration from diagram context.
        
        Args:
            person_id: The person ID to look up
            context: The execution context containing diagram data
            
        Returns:
            Person configuration dict if found, None otherwise
        """
        if not context.diagram:
            return None
            
        persons = context.diagram.get('persons', [])
        for person in persons:
            if person.get('id') == person_id:
                return person
        
        return None
    
    def _aggregate_results(self, results: List[Any], data: dict) -> Any:
        """Aggregate batch results based on configuration."""
        aggregation = data.get('aggregation', 'list')
        
        if aggregation == 'list':
            return results
        elif aggregation == 'concat':
            # Concatenate string results
            return '\n'.join(str(r) for r in results if r is not None)
        elif aggregation == 'json':
            # Return as JSON array
            return [r for r in results if r is not None]
        elif aggregation == 'first':
            return results[0] if results else None
        elif aggregation == 'last':
            return results[-1] if results else None
        else:
            return results