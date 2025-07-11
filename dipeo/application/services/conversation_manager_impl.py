# Implementation of ConversationManager protocol using Person and PersonManager.

import json
from datetime import datetime
from typing import Any

from pathlib import Path
from dipeo.core import BaseService
from dipeo.core.dynamic.conversation import Conversation
from dipeo.core.dynamic.conversation_manager import ConversationManager
from dipeo.core.utils import is_conversation
from dipeo.models import (
    ApiKeyID,
    ForgettingMode,
    LLMService,
    Message,
    PersonID,
    PersonLLMConfig,
)
from dipeo.application.services.person_manager_impl import PersonManagerImpl
from dipeo.core.dynamic.memory_filters import (
    MemoryView, MemoryFilterFactory, MemoryLimiter
)
from dipeo.core.dynamic.forgetting_strategies import ForgettingStrategyFactory


class ConversationManagerImpl(BaseService, ConversationManager):
    # Maintains a single global conversation that all persons share
    
    def __init__(self):
        super().__init__()
        self.person_manager = PersonManagerImpl()
        self._current_execution_id: str | None = None
        self._conversation_logs: dict[str, list[dict[str, Any]]] = {}
        # Single global conversation shared by all persons
        self._global_conversation = Conversation()
    
    def get_conversation(self, person_id: str = "") -> Conversation:
        """Get the global conversation. person_id parameter is ignored (backward compatibility)."""
        return self._global_conversation
    
    
    def add_message(
        self,
        message: Message,
        execution_id: str,
        node_id: str | None = None
    ) -> None:
        """Add a message to the global conversation and route to relevant persons."""
        self._current_execution_id = execution_id
        
        # Add to global conversation
        self._global_conversation.add_message(message)
        
        # Route to sender (if not system)
        if message.from_person_id != "system":
            self._add_to_person_conversation(
                str(message.from_person_id), 
                message, 
                execution_id, 
                node_id
            )
        
        # Route to recipient (if not system and different from sender)
        if message.to_person_id != "system" and message.to_person_id != message.from_person_id:
            self._add_to_person_conversation(
                str(message.to_person_id), 
                message, 
                execution_id, 
                node_id
            )
    
    def _add_to_person_conversation(
        self,
        person_id: str,
        message: Message,
        execution_id: str,
        node_id: str | None = None
    ) -> None:
        """Route message to person's memory view."""
        person_id_obj = PersonID(person_id)
        if not self.person_manager.person_exists(person_id_obj):
            return
        
        person = self.person_manager.get_person(person_id_obj)
        person.add_message(message)
        
        # Log for persistence
        if execution_id not in self._conversation_logs:
            self._conversation_logs[execution_id] = []
        self._conversation_logs[execution_id].append({
            "person_id": person_id,
            "role": self._get_role_from_message(message),
            "content": message.content,
            "from_person_id": str(message.from_person_id),
            "to_person_id": str(message.to_person_id),
            "node_id": node_id,
            "timestamp": message.timestamp
        })
    
    def apply_forgetting(
        self,
        person_id: str,
        mode: ForgettingMode,
        execution_id: str | None = None,
        execution_count: int = 0
    ) -> int:
        """Apply forgetting strategy to a person's memory view.
        
        Note: In the global conversation model, forgetting doesn't delete messages
        from the global conversation. Instead, it changes what the person "remembers"
        by adjusting their memory view or filters.
        """
        person_id_obj = PersonID(person_id)
        
        if not self.person_manager.person_exists(person_id_obj):
            return 0
        
        person = self.person_manager.get_person(person_id_obj)
        
        # Create forgetting strategy
        strategy = ForgettingStrategyFactory.create(mode)
        
        # Create a minimal memory config if needed
        from dipeo.models import MemoryConfig
        memory_config = MemoryConfig(forget_mode=mode)
        
        # Apply the strategy
        return strategy.apply(person, memory_config, execution_count)
    
    
    
    
    
    
    def _dict_to_message(self, msg_dict: dict[str, Any], person_id: str) -> Message | None:
        if self._current_execution_id and msg_dict.get("execution_id") != self._current_execution_id:
            return None
        
        from_person_id = msg_dict.get("from_person_id", msg_dict.get("current_person_id", person_id))
        to_person_id = msg_dict.get("to_person_id", person_id)
        
        role = msg_dict.get("role", "user")
        if role == "system":
            from_person_id = "system"
            message_type = "system_to_person"
        elif role == "external":
            message_type = "person_to_person"
        else:
            message_type = "person_to_person"
        
        return Message(
            from_person_id=PersonID(from_person_id) if from_person_id != "system" else "system",  # type: ignore
            to_person_id=PersonID(to_person_id) if to_person_id != "system" else "system",  # type: ignore
            content=msg_dict.get("content", ""),
            timestamp=msg_dict.get("timestamp"),
            message_type=message_type,  # type: ignore
            metadata={"role": role, "node_id": msg_dict.get("node_id")}
        )
    
    @staticmethod
    def _get_role_from_message(message: Message) -> str:
        if message.from_person_id == "system":
            return "system"
        elif message.from_person_id == message.to_person_id:
            return "assistant"
        else:
            return "user"
    
    def set_execution_id(self, execution_id: str) -> None:
        self._current_execution_id = execution_id
    
    
    async def initialize(self) -> None:
        """Initialize the conversation manager and set it on all persons."""
        # Set conversation manager on all existing persons
        for person in self.person_manager.get_all_persons().values():
            person._conversation_manager = self
    
    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        
        person_id_obj = PersonID(person_id)
        if not self.person_manager.person_exists(person_id_obj):
            llm_config = PersonLLMConfig(
                service=LLMService(config.get('service', 'openai')),
                model=config.get('model', 'gpt-4'),
                api_key_id=ApiKeyID(config.get('api_key_id', 'default')),
                system_prompt=config.get('system_prompt'),
                temperature=config.get('temperature'),
                max_tokens=config.get('max_tokens')
            )
            # Use create_person method instead of accessing _persons directly
            person = self.person_manager.create_person(
                person_id=person_id_obj,
                name=config.get('name', person_id),
                llm_config=llm_config
            )
            # Set conversation manager on the newly created person
            person._conversation_manager = self
    
    def get_person_config(self, person_id: str) -> dict[str, Any] | None:
        person_id_obj = PersonID(person_id)
        if self.person_manager.person_exists(person_id_obj):
            person = self.person_manager.get_person(person_id_obj)
            if person.llm_config:
                return {
                    'service': person.llm_config.service.value,
                    'model': person.llm_config.model,
                    'api_key_id': str(person.llm_config.api_key_id),
                    'system_prompt': person.llm_config.system_prompt,
                    'temperature': person.llm_config.temperature,
                    'max_tokens': person.llm_config.max_tokens
                }
        return None
    
    
    
    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        """Get conversation history from person's memory view."""
        person_id_obj = PersonID(person_id)
        if not self.person_manager.person_exists(person_id_obj):
            return []
        
        person = self.person_manager.get_person(person_id_obj)
        history = []
        
        # Get messages from person's filtered view
        for msg in person.get_messages():
            role = "assistant" if msg.from_person_id == person_id else "user"
            if msg.from_person_id == "system":
                role = "system"
            
            history.append({
                "role": role,
                "content": msg.content,
                "from_person_id": str(msg.from_person_id),
                "to_person_id": str(msg.to_person_id),
                "execution_id": self._current_execution_id,
                "timestamp": msg.timestamp,
                "node_id": msg.metadata.get("node_id") if msg.metadata else None
            })
        
        return history
    
    
    
    def clear_all_conversations(self) -> None:
        """Clear the global conversation and all person memories."""
        # Clear global conversation
        self._global_conversation.clear()
        
        # Clear each person's memory view
        for person_id, person in self.person_manager.get_all_persons().items():
            person.clear_conversation()
        
        # Clear logs
        self._conversation_logs.clear()
    
    async def save_conversation_log(self, execution_id: str, log_dir: Path) -> str:
        import json
        from datetime import datetime
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"conversation_{execution_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = log_dir / filename
        
        # Save the global conversation
        global_messages = []
        for msg in self._global_conversation.messages:
            global_messages.append({
                "role": self._get_role_from_message(msg),
                "content": msg.content,
                "from_person_id": str(msg.from_person_id),
                "to_person_id": str(msg.to_person_id),
                "timestamp": msg.timestamp
            })
        
        # Also create per-person views for backward compatibility
        conversations = {}
        for person_id, person in self.person_manager.get_all_persons().items():
            messages = []
            for msg in person.get_messages():
                messages.append({
                    "role": self._get_role_from_message(msg),
                    "content": msg.content,
                    "from_person_id": str(msg.from_person_id),
                    "to_person_id": str(msg.to_person_id),
                    "timestamp": msg.timestamp
                })
            conversations[str(person_id)] = messages
        
        with open(filepath, 'w') as f:
            json.dump({
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
                "global_conversation": global_messages,
                "conversations": conversations  # Backward compatibility
            }, f, indent=2)
        
        return str(filepath)
    
    @staticmethod
    def is_conversation(value: Any) -> bool:
        return is_conversation(value)
    
    
    
    
    
    
    
