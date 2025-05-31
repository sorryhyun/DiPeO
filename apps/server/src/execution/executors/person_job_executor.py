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
        
        # Pre-initialize LLM clients for each person
        self.person_llm_clients = {}
        self._initialize_person_clients()
    
    def _initialize_person_clients(self):
        """Initialize LLM clients for each person in the diagram."""
        if not self.context.diagram or 'persons' not in self.context.diagram:
            return
        
        persons = self.context.diagram['persons']
        for person in persons:
            try:
                person_id = person.get('id')
                model_name = person.get('modelName')
                api_key_name = person.get('apiKeyId')
                
                if model_name and api_key_name and self.llm_service:
                    # Get the adapter for this person's configuration
                    service = self._extract_service_from_model(model_name)
                    client = self.llm_service._get_client(service, model_name, api_key_name)
                    self.person_llm_clients[person_id] = client
            except Exception as e:
                print(f"[WARNING] Failed to initialize LLM client for person {person_id}: {e}")
    
    def _extract_service_from_model(self, model_name: str) -> str:
        """Extract service name from model name."""
        model_lower = model_name.lower()
        if 'gpt' in model_lower or 'o1' in model_lower:
            return 'openai'
        elif 'claude' in model_lower:
            return 'claude'
        elif 'gemini' in model_lower:
            return 'gemini'
        elif 'grok' in model_lower:
            return 'grok'
        else:
            return 'openai'  # Default fallback
    
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
        
        # Get person ID and use pre-initialized client
        person_id = self._get_node_property(node, 'data.personId')
        
        # Use pre-initialized LLM client for this person
        if person_id in self.person_llm_clients:
            client = self.person_llm_clients[person_id]
            
            # Call LLM directly with adapter
            response = await self.llm_service._call_llm_with_retry(
                client=client,
                system_prompt="",  # Will be extracted from prompt if needed
                user_prompt=prompt
            )
            
            # Extract result and calculate cost
            text, usage = self.llm_service._extract_result_and_usage(response)
            cost = self.llm_service.calculate_cost('openai', usage)
            
            response_obj = type('Response', (), {'text': text, 'cost': cost})()
        else:
            # Fallback to old method if client not initialized
            model = self._get_person_property(person_id, 'modelName')
            api_key_name = self._get_node_property(node, 'data.apiKeyName')
            
            response = await self.llm_service.call_llm(
                prompt=prompt,
                model=model,
                api_key_name=api_key_name
            )
            response_obj = response
        
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
                content=response_obj.text
            )
        
        return response_obj.text, response_obj.cost
    
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
        person_id = self._get_node_property(node, 'data.personId')
        if person_id:
            memory_context = self.memory_service.get_conversation_history(person_id)
            if memory_context: prompt = f"{memory_context}\n\n{prompt}"
            else: pass
        
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
        if not (self._get_node_property(node, 'data.defaultPrompt')
                or self._get_node_property(node, 'data.firstOnlyPrompt')):
            return "PersonJob node requires a prompt"

        for person in self.context.diagram['persons']:
            if person['id'] == self._get_node_property(node, 'data.personId'):
                if not person['modelName']:
                    return "PersonJob node requires a model selection"
        
        return None