# Implementation of ConversationManager protocol using Person and PersonManager.

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dipeo.application.services.person_manager_impl import PersonManagerImpl
from dipeo.core import BaseService
from dipeo.domain.conversation.conversation import Conversation
from dipeo.domain.conversation.conversation_manager import ConversationManager
from dipeo.core.utils import is_conversation
from dipeo.diagram_generated import (
    ApiKeyID,
    LLMService,
    Message,
    PersonID,
    PersonLLMConfig,
)


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
        """Get the global conversation."""
        # person_id parameter is ignored - all persons share the same conversation
        return self._global_conversation
    
    
    def add_message(
        self,
        message: Message,
        execution_id: str,
        node_id: str | None = None
    ) -> None:
        """Add a message to the global conversation."""
        self._current_execution_id = execution_id
        
        # Add to global conversation
        self._global_conversation.add_message(message)
        
        # Log for persistence
        if execution_id not in self._conversation_logs:
            self._conversation_logs[execution_id] = []
        
        self._conversation_logs[execution_id].append({
            "role": self._get_role_from_message(message),
            "content": message.content,
            "from_person_id": str(message.from_person_id),
            "to_person_id": str(message.to_person_id),
            "node_id": node_id,
            "timestamp": message.timestamp
        })
    
    # Removed _add_to_person_conversation - no longer needed
    
    
    @staticmethod
    def _get_role_from_message(message: Message) -> str:
        if message.from_person_id == "system":
            return "system"
        elif message.from_person_id == message.to_person_id:
            return "assistant"
        else:
            return "user"
    
    async def initialize(self) -> None:
        """Initialize the conversation manager and set it on all persons."""
        # Set conversation manager on all existing persons
        for person in self.person_manager.get_all_persons().values():
            person._conversation_manager = self
    
    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"ConversationManager.register_person called for {person_id} with config: {config}")
        person_id_obj = PersonID(person_id)
        if not self.person_manager.person_exists(person_id_obj):
            api_key_id_value = config.get('api_key_id', 'default')
            logger.debug(f"Creating PersonLLMConfig with api_key_id: {api_key_id_value}")
            llm_config = PersonLLMConfig(
                service=LLMService(config.get('service', 'openai')),
                model=config.get('model', 'gpt-4'),
                api_key_id=ApiKeyID(api_key_id_value)
            )
            logger.debug(f"Created PersonLLMConfig: service={llm_config.service}, model={llm_config.model}, api_key_id={llm_config.api_key_id}")
            # Use create_person method instead of accessing _persons directly
            person = self.person_manager.create_person(
                person_id=person_id_obj,
                name=config.get('name', person_id),
                llm_config=llm_config
            )
            # Set conversation manager on the newly created person
            person._conversation_manager = self
            logger.debug(f"Person {person_id} created successfully")
        else:
            logger.debug(f"Person {person_id} already exists, skipping creation")
    
    def get_person_config(self, person_id: str) -> PersonLLMConfig | None:
        person_id_obj = PersonID(person_id)
        if self.person_manager.person_exists(person_id_obj):
            person = self.person_manager.get_person(person_id_obj)
            if person.llm_config:
                return person.llm_config
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
        
        # Reset each person's memory limits
        for person_id, person in self.person_manager.get_all_persons().items():
            # Reset memory configuration
            person.set_memory_limit(-1)  # Remove limit
        
        # Clear logs
        self._conversation_logs.clear()
    
    async def save_conversation_log(self, execution_id: str, log_dir: Path) -> str:
        
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
        
        with open(filepath, 'w') as f:
            json.dump({
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
                "global_conversation": global_messages
            }, f, indent=2)
        
        return str(filepath)
    
    @staticmethod
    def is_conversation(value: Any) -> bool:
        return is_conversation(value)