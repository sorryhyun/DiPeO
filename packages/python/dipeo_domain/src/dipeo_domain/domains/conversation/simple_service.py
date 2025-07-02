# Simplified conversation memory service focused on essential features.

import re
from typing import Any, Dict, List, Optional, Tuple

from dipeo_core import BaseService, SupportsMemory


class ConversationMemoryService(BaseService, SupportsMemory):
    # Minimal conversation memory for person_job nodes.
    # Supports system, user, assistant, and external message roles.

    def __init__(self):
        super().__init__()
        # Simple structure: {person_id: [messages]}
        self._conversations: Dict[str, List[Dict[str, str]]] = {}

    async def initialize(self) -> None:
        pass

    def add_message_to_conversation(
        self,
        person_id: str,
        execution_id: str,  # Required by interface but not used
        role: str,
        content: str,
        current_person_id: str,  # Required by interface but not used
        node_id: Optional[str] = None,  # Required by interface but not used
        timestamp: Optional[float] = None,  # Required by interface but not used
    ) -> None:
        """Main method to add a message. Extra parameters exist for interface compatibility but are ignored."""
        if person_id not in self._conversations:
            self._conversations[person_id] = []
        
        self._conversations[person_id].append({"role": role, "content": content})
    
    def add_message(self, person_id: str, role: str, content: str) -> None:
        """Simplified method that delegates to add_message_to_conversation."""
        self.add_message_to_conversation(
            person_id=person_id,
            execution_id="",
            role=role,
            content=content,
            current_person_id=""
        )

    def get_messages(self, person_id: str) -> List[Dict[str, str]]:
        return self._conversations.get(person_id, [])

    def _clear_messages(
        self, 
        person_id: str, 
        keep_system: bool = True,
        keep_user: bool = True,
        keep_assistant: bool = True,
        keep_external: bool = True
    ) -> None:
        """Internal method to clear messages with fine-grained control.
        
        By default keeps all messages. Set parameters to False to clear specific roles.
        """
        if person_id not in self._conversations:
            return

        roles_to_keep = set()
        if keep_system:
            roles_to_keep.add("system")
        if keep_user:
            roles_to_keep.add("user")
        if keep_assistant:
            roles_to_keep.add("assistant")
        if keep_external:
            roles_to_keep.add("external")

        self._conversations[person_id] = [
            msg for msg in self._conversations[person_id] 
            if msg["role"] in roles_to_keep
        ]

    def get_or_create_person_memory(self, person_id: str) -> None:
        # No-op: initialization happens automatically in add_message_to_conversation
        pass

    def get_conversation_history(self, person_id: str) -> List[Dict[str, str]]:
        # Interface method - delegates to get_messages
        return self.get_messages(person_id)

    def forget_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        # Interface method - clear all messages
        self._clear_messages(person_id, keep_system=False, keep_user=False, 
                           keep_assistant=False, keep_external=False)

    def forget_own_messages_for_person(
        self, person_id: str, execution_id: Optional[str] = None
    ) -> None:
        # Interface method - clear only assistant messages
        self._clear_messages(person_id, keep_system=True, keep_user=True, 
                           keep_assistant=False, keep_external=True)

    def clear_all_conversations(self) -> None:
        self._conversations.clear()

    async def save_conversation_log(self, execution_id: str, log_dir: any) -> str:
        return f"{log_dir}/conversation_{execution_id}.json"
    
    def get_messages_for_output(self, person_id: str, forget_mode: Optional[str] = None) -> List[Dict[str, str]]:
        """Get messages to pass to downstream nodes, respecting forgetting mode."""
        messages = self.get_messages(person_id)
        
        # For on_every_turn mode, only return the last assistant message
        if forget_mode == "on_every_turn":
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    return [msg]
            return []  # No assistant message found
        
        # For other modes, return all messages
        return messages
    
    def prepare_messages_for_llm(self, person_id: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Prepare messages for LLM call, handling external role conversion."""
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation messages, converting external to system
        for msg in self.get_messages(person_id):
            # Convert external messages to system role for LLM compatibility
            role = "system" if msg["role"] == "external" else msg["role"]
            messages.append({"role": role, "content": msg["content"]})
        
        return messages
    
    
    @staticmethod
    def substitute_template(template: str, values: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
        """Substitute {{placeholders}} in template with values.
        
        Note: This is a utility method that could be moved to a separate utilities module.
        
        Returns:
            tuple: (substituted_string, list_of_missing_keys, list_of_used_keys)
        """
        missing_keys = []
        used_keys = []
        
        def replacer(match):
            key = match.group(1)
            if key in values:
                used_keys.append(key)
                return str(values[key])
            else:
                missing_keys.append(key)
                return match.group(0)  # Keep original placeholder
        
        # Match {{key}} pattern
        pattern = r'\{\{(\w+)\}\}'
        result = re.sub(pattern, replacer, template)
        
        return result, missing_keys, used_keys
    
    def get_messages_with_person_id(self, person_id: str, forget_mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get messages for output with person_id attached."""
        messages = self.get_messages_for_output(person_id, forget_mode)
        
        # Add personId to each message
        messages_with_id = []
        for msg in messages:
            msg_with_person = msg.copy()
            msg_with_person["person_id"] = person_id
            messages_with_id.append(msg_with_person)
        
        return messages_with_id
    
    def process_conversation_inputs(
        self,
        person_id: str,
        inputs: Dict[str, Any],
        prompt: Optional[str] = None,
        used_template_keys: Optional[set] = None,
        diagram: Optional[Any] = None
    ) -> Optional[str]:
        """Process conversation inputs and return remaining prompt if any.
        
        Simplifies conversation handling by:
        1. Extracting the last opponent message from conversation data
        2. Formatting it with opponent label and developer prompt
        3. Adding as a single user message
        
        Returns:
            Optional[str]: The prompt if it wasn't consumed, None otherwise.
        """
        if used_template_keys is None:
            used_template_keys = set()
        
        prompt_consumed = False
        
        for key, value in inputs.items():
            if not value or key in used_template_keys:
                continue
                
            # Check if this is conversation data
            is_conversation = (
                key == "conversation" or 
                (key == "default" and 
                 isinstance(value, list) and 
                 value and 
                 isinstance(value[0], dict) and 
                 "role" in value[0])
            )
            
            if is_conversation:
                # Extract opponent's last message
                opponent_message = self._extract_last_message(value)
                
                # Build formatted message
                message_parts = []
                
                if opponent_message:
                    opponent_label = self._get_opponent_label(opponent_message, diagram)
                    message_parts.append(f"[{opponent_label}]: {opponent_message['content']}")
                
                if prompt:
                    message_parts.append(f"[developer]: {prompt}")
                    prompt_consumed = True
                
                # Add as a single user message
                if message_parts:
                    self.add_message_to_conversation(
                        person_id=person_id,
                        execution_id="",
                        role="user",
                        content="\n".join(message_parts),
                        current_person_id=""
                    )
            else:
                # Other non-conversation inputs - add as user message
                self.add_message_to_conversation(
                    person_id=person_id,
                    execution_id="",
                    role="user",
                    content=str(value),
                    current_person_id=""
                )
        
        return None if prompt_consumed else prompt
    
    @staticmethod
    def _extract_last_message(conversation_value: Any) -> Optional[Dict[str, str]]:
        """Extract the last relevant message from conversation data."""
        if not isinstance(conversation_value, list) or not conversation_value:
            return None
            
        # For on_every_turn mode, we expect only one message
        if len(conversation_value) == 1:
            return conversation_value[0]
        
        # Otherwise, find the last assistant message
        for msg in reversed(conversation_value):
            if msg.get("role") == "assistant":
                return msg
        
        # Fallback to last message
        return conversation_value[-1]
    
    @staticmethod
    def _get_opponent_label(message: Dict[str, str], diagram: Optional[Any]) -> str:
        """Get the label for the opponent from the message and diagram."""
        if "person_id" not in message or not diagram:
            return "Opponent"
            
        person_id = message["person_id"]
        for person in getattr(diagram, "persons", []):
            if person.id == person_id:
                return person.label or person_id
                
        return "Opponent"
