"""
PersonBatchJob node executor for batch LLM agent interactions.
Handles batch processing with LLM agents and result aggregation.
"""
from typing import Any, Dict, Optional, List
import asyncio
import logging

from .base_executor import BaseExecutor
from ...constants import NodeType
from ...utils.resolve_utils import render_prompt

logger = logging.getLogger(__name__)


class PersonBatchJobExecutor(BaseExecutor):
    """Executes PersonBatchJob nodes for batch processing with LLM agents."""
    
    node_type = NodeType.PERSON_BATCH_JOB
    
    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Validate PersonBatchJob node inputs."""
        data = self.node.get('data', {})
        
        if not data.get('personId'):
            raise ValueError("PersonBatchJob requires 'personId'")
        
        if not data.get('prompt'):
            raise ValueError("PersonBatchJob requires 'prompt'")
        
        # Validate person exists
        person_id = data['personId']
        persons = self.context.diagram.persons or []
        if not any(p['id'] == person_id for p in persons):
            raise ValueError(f"Person '{person_id}' not found in diagram")
    
    async def execute_node(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the PersonBatchJob node logic."""
        data = self.node.get('data', {})
        person_id = data['personId']
        prompt_template = data.get('prompt', '')
        batch_size = data.get('batchSize', 5)
        parallel = data.get('parallel', False)
        
        # Get person configuration
        person = next((p for p in self.context.diagram.persons if p['id'] == person_id), None)
        if not person:
            raise ValueError(f"Person '{person_id}' not found")
        
        # Prepare inputs
        input_list = self._prepare_inputs(inputs)
        if not input_list:
            logger.warning(f"PersonBatchJob {self.node_id} has no inputs to process")
            return {'value': [], 'cost': 0.0}
        
        # Create vars_map
        vars_map = {}
        for node_id, output in self.context.outputs.items():
            vars_map[node_id] = self._resolve_value(f"{{{{{node_id}}}}}")
        
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
        
        return {
            'value': aggregated,
            'cost': total_cost,
            'metadata': {
                'batch_count': len(results),
                'person_id': person_id
            }
        }
    
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
        
        # Get conversation history
        conversation = self.memory_service.get_conversation_history(person['id'])
        
        # Add user message
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
            
            # Add assistant response to memory
            self.memory_service.add_message(person['id'], 'assistant', response)
            
            return response, cost
            
        except Exception as e:
            logger.error(f"Failed to process batch item: {e}")
            return None, 0.0
    
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