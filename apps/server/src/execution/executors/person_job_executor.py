"""Simplified PersonJob executor for the new architecture."""

from typing import Any, Dict, Tuple, Optional

from .base_executor import BaseExecutor
from ..core.execution_context import ExecutionContext
from ..core.skip_manager import SkipManager


class PersonJobExecutor(BaseExecutor):
    """Executor for PersonJob nodes - handles LLM interactions with memory."""
    
    def __init__(self, context: ExecutionContext, llm_service=None, memory_service=None):
        """Initialize with required services.
        
        Args:
            context: The execution context
            llm_service: Service for LLM interactions
            memory_service: Service for memory management
        """
        super().__init__(context, llm_service, memory_service)
    
    async def execute(
        self,
        node: Dict[str, Any],
        context: ExecutionContext,
        skip_manager: SkipManager,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a PersonJob node.
        
        This simplified version focuses solely on execution logic,
        leaving skip decisions and memory management to specialized components.
        
        Args:
            node: The node configuration
            context: The execution context
            skip_manager: The skip manager (not used here, decisions made by engine)
            **kwargs: Additional arguments
            
        Returns:
            Tuple of (response_text, cost)
        """
        node_id = node['id']
        
        # Prepare inputs
        inputs = self._prepare_inputs(node, context)
        
        # Build prompt
        prompt = await self._build_prompt(node, inputs, context)
        
        # Get person and model info
        person_id = self._get_node_property(node, 'data.person.id')
        model = self._get_node_property(node, 'data.model')
        api_key_name = self._get_node_property(node, 'data.apiKeyName')
        
        # Call LLM
        response = await self.llm_service.call_llm(
            prompt=prompt,
            model=model,
            api_key_name=api_key_name
        )
        
        # Let memory service handle memory updates
        if person_id:
            await self.memory_service.add_message(
                person_id=person_id,
                role="user",
                content=prompt
            )
            await self.memory_service.add_message(
                person_id=person_id,
                role="assistant",
                content=response.text
            )
        
        return response.text, response.cost
    
    async def _build_prompt(
        self,
        node: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> str:
        """Build the prompt for the LLM.
        
        Args:
            node: The node configuration
            inputs: Resolved input values
            context: The execution context
            
        Returns:
            The constructed prompt string
        """
        # Get base prompt
        prompt = inputs.get('prompt', '')
        
        # Add system prompt if exists
        system_prompt = inputs.get('systemPrompt', '')
        if system_prompt:
            prompt = f"{system_prompt}\n\n{prompt}"
        
        # Add memory context if person has memory
        person_id = self._get_node_property(node, 'data.person.id')
        if person_id:
            memory_context = await self.memory_service.get_memory_context(person_id)
            if memory_context:
                prompt = f"{memory_context}\n\n{prompt}"
        
        return prompt
    
    async def validate_inputs(
        self,
        node: Dict[str, Any],
        context: ExecutionContext
    ) -> Optional[str]:
        """Validate PersonJob node inputs.
        
        Args:
            node: The node configuration
            context: The execution context
            
        Returns:
            Error message if validation fails, None if valid
        """
        # Check for required fields
        if not self._get_node_property(node, 'data.prompt'):
            return "PersonJob node requires a prompt"
        
        if not self._get_node_property(node, 'data.model'):
            return "PersonJob node requires a model selection"
        
        if not self._get_node_property(node, 'data.apiKeyName'):
            return "PersonJob node requires an API key selection"
        
        return None