"""Simplified PersonJob executor with clear separation of concerns."""

import logging
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from collections import Counter

from .state import ExecutionState
from ..services.memory_service import MemoryService
from ..services.llm_service import LLMService
from ..utils.resolve_utils import render_prompt
from ..utils.output_processor import OutputProcessor

logger = logging.getLogger(__name__)


class PersonJobExecutor:
    """Simplified PersonJob executor with clear separation of concerns."""
    
    def __init__(self, memory_service: MemoryService, llm_service: LLMService, execution_id: str):
        self.memory_service = memory_service
        self.llm_service = llm_service
        self.execution_id = execution_id
    
    async def execute(self, node: dict, person: dict, vars_map: Dict[str, Any], 
                     incoming_arrows: List[dict], state: ExecutionState,
                     arrow_src_fn, send_status_update_fn, get_all_person_ids_fn) -> Tuple[Any, float]:
        """Execute a PersonJob node with simplified logic.
        
        Args:
            node: Node configuration
            person: Person configuration
            vars_map: Variable mappings for prompt rendering
            incoming_arrows: Incoming arrows with data
            state: Current execution state
            arrow_src_fn: Function to get arrow source
            send_status_update_fn: Callback for status updates
            get_all_person_ids_fn: Function to get all person IDs
            
        Returns:
            Tuple of (response, cost)
        """
        node_id = node["id"]
        person_id = node.get("data", {}).get("personId")
        iteration = state.counts[node_id]
        
        # Skip if at max iterations (no memory operations)
        if self.is_at_max_iterations(node, state):
            return self.skip_result(), 0.0
        
        # Clear separation of concerns
        memory_state = self.prepare_memory(node, person_id)
        conversation_data = self.process_incoming_data(incoming_arrows, arrow_src_fn, state.context)
        prompt = self.build_prompt(node, vars_map, conversation_data, iteration)
        
        # Add user message to memory if there's content
        if prompt.strip():
            self.add_user_message_to_memory(prompt, person_id, node, get_all_person_ids_fn)
        
        # Call LLM
        response = await self.call_llm(prompt, person, conversation_data)
        
        # Update memory and send status update
        self.update_memory(response, person_id, node, get_all_person_ids_fn)
        await self.send_status_update(response, person_id, node, send_status_update_fn)
        
        # Build output
        output = self.build_output(response, conversation_data, person_id, person.get("modelName"))
        
        return output, response.get("cost", 0.0)
    
    def is_at_max_iterations(self, node: dict, state: ExecutionState) -> bool:
        """Check if node is at max iterations."""
        node_id = node["id"]
        max_iter = state.node_max_iterations.get(node_id)
        return max_iter and state.counts[node_id] >= max_iter
    
    def skip_result(self) -> dict:
        """Return result for skipped execution."""
        return {"skipped_max_iter": True}
    
    def prepare_memory(self, node: dict, person_id: str) -> dict:
        """Prepare memory state based on node configuration."""
        data = node.get("data", {})
        
        # Handle memory forget mode
        forget_mode = data.get("memoryForget", "none")
        if forget_mode == "all":
            self.memory_service.forget_for_person(person_id)
        elif forget_mode == "current_execution":
            self.memory_service.forget_for_person(person_id, self.execution_id)
        
        # Handle context cleaning rule
        if data.get("contextCleaningRule") == "on_every_turn":
            self.memory_service.forget_for_person(person_id, self.execution_id)
            return {"own_conversation_history": []}
        else:
            return {"own_conversation_history": self.memory_service.get_conversation_history(person_id)}
    
    def process_incoming_data(self, incoming_arrows: List[dict], arrow_src_fn, context: Dict[str, Any]) -> dict:
        """Process incoming arrows to extract conversation and preamble data."""
        incoming_conversation = []
        preamble_parts = []
        
        for arrow in incoming_arrows:
            src_id = arrow_src_fn(arrow)
            if not src_id or src_id not in context:
                continue
            
            src_value = context[src_id]
            content_type = arrow.get("data", {}).get("contentType", "raw_text")
            
            if content_type == "conversation_state":
                conversation = self._extract_conversation(src_value)
                incoming_conversation.extend(conversation)
            elif content_type in {"file", "whole"}:
                extracted_value = OutputProcessor.extract_value(src_value)
                preamble_parts.append(str(extracted_value))
        
        return {
            "incoming_conversation": incoming_conversation,
            "preamble_parts": preamble_parts
        }
    
    def _extract_conversation(self, src_value: Any) -> List[dict]:
        """Extract conversation history from source value."""
        if OutputProcessor.is_personjob_output(src_value):
            return OutputProcessor.extract_conversation_history(src_value)
        elif isinstance(src_value, list) and all(
            isinstance(msg, dict) and 'role' in msg and 'content' in msg for msg in src_value
        ):
            return src_value
        else:
            # Fallback: treat as a user message
            return [{"role": "user", "content": str(src_value)}]
    
    def build_prompt(self, node: dict, vars_map: Dict[str, Any], conversation_data: dict, iteration: int) -> str:
        """Build the prompt for LLM call."""
        data = node.get("data", {})
        
        # Choose appropriate template
        first_prompt = data.get("firstOnlyPrompt")
        default_prompt = data.get("defaultPrompt")
        template = first_prompt if iteration == 1 and first_prompt else default_prompt
        
        # Render prompt with variables
        return render_prompt(template, vars_map)
    
    def build_messages(self, prompt: str, conversation_data: dict, memory_state: dict) -> List[dict]:
        """Build message list for LLM call."""
        messages = []
        
        # Add incoming conversation or own history
        if conversation_data["incoming_conversation"]:
            messages.extend(conversation_data["incoming_conversation"])
        elif memory_state["own_conversation_history"]:
            messages.extend(memory_state["own_conversation_history"])
        
        # Add prompt with preamble if needed
        if conversation_data["preamble_parts"] and prompt.strip():
            full_prompt = "\n\n".join(conversation_data["preamble_parts"] + [prompt])
            messages.append({"role": "user", "content": full_prompt})
        elif prompt.strip():
            messages.append({"role": "user", "content": prompt})
        
        # Default message if none
        if not messages and not prompt.strip():
            messages.append({"role": "user", "content": "Continue the conversation."})
        
        return messages
    
    async def call_llm(self, prompt: str, person: dict, conversation_data: dict) -> dict:
        """Call the LLM with configured parameters."""
        memory_state = {"own_conversation_history": self.memory_service.get_conversation_history(person.get("id", ""))}
        messages = self.build_messages(prompt, conversation_data, memory_state)
        
        # Get model configuration
        model_name = person.get("modelName")
        service = person.get("service")
        api_key_id = person.get("apiKeyId")
        
        # Auto-detect service if needed
        if not service and model_name and "gpt" in model_name.lower():
            service = "openai"
            if not api_key_id:
                api_key_id = await self._find_default_api_key(service)
        
        # Handle specific model naming
        if model_name == "gpt-4.1-nano":
            model_name = "gpt-4.1-nano-2025-04-14"
        
        return await self.llm_service.call_llm(
            messages=messages,
            service=service,
            model=model_name,
            api_key_id=api_key_id,
            system_prompt=person.get("systemPrompt", ""),
        )
    
    def add_user_message_to_memory(self, prompt: str, person_id: str, node: dict, get_all_person_ids_fn):
        """Add user message to conversation memory."""
        if prompt.strip():
            self.memory_service.add_message_to_conversation(
                content=prompt,
                sender_person_id=person_id,
                execution_id=self.execution_id,
                participant_person_ids=get_all_person_ids_fn(),
                role="user",
                node_id=node["id"],
                node_label=node.get("data", {}).get("label", "PersonJob"),
                token_count=int(len(prompt.split()) * 1.3),
                cost=0.0
            )
    
    def update_memory(self, response: dict, person_id: str, node: dict, get_all_person_ids_fn):
        """Update memory with assistant response."""
        result_text = response.get("response", "")
        cost = response.get("cost", 0.0)
        token_count = len(result_text.split()) * 1.3
        
        self.memory_service.add_message_to_conversation(
            content=result_text,
            sender_person_id=person_id,
            execution_id=self.execution_id,
            participant_person_ids=get_all_person_ids_fn(),
            role="assistant",
            node_id=node["id"],
            node_label=node.get("data", {}).get("label", "PersonJob"),
            token_count=int(token_count),
            cost=cost
        )
    
    async def send_status_update(self, response: dict, person_id: str, node: dict, send_status_update_fn):
        """Send status update for the response."""
        result_text = response.get("response", "")
        cost = response.get("cost", 0.0)
        token_count = len(result_text.split()) * 1.3
        
        await send_status_update_fn(
            "message_added", node["id"],
            message={
                "content": result_text,
                "sender_person_id": person_id,
                "timestamp": datetime.now().isoformat(),
                "node_id": node["id"],
                "node_label": node.get("data", {}).get("label"),
                "cost": cost,
                "token_count": int(token_count)
            }
        )
    
    def build_output(self, response: dict, conversation_data: dict, person_id: str, model_name: str) -> dict:
        """Build the complete output structure."""
        result_text = response.get("response", "")
        cost = response.get("cost", 0.0)
        
        # Build conversation history for output
        output_conversation = []
        if conversation_data["incoming_conversation"]:
            output_conversation.extend(conversation_data["incoming_conversation"])
        # Add the response
        output_conversation.append({"role": "assistant", "content": result_text})
        
        # Create structured output
        output = OutputProcessor.create_personjob_output(
            text=result_text,
            conversation_history=output_conversation,
            cost=cost,
            model=model_name
        )
        output["person_id"] = person_id
        
        return output
    
    async def _find_default_api_key(self, service: str) -> Optional[str]:
        """Find default API key for service."""
        from ..services.api_key_service import APIKeyService
        api_key_service = APIKeyService()
        keys = api_key_service.list_api_keys()
        for key in keys:
            if key["service"] == service:
                return key["id"]
        return None