"""Execution orchestrator that coordinates repositories during diagram execution."""

import logging
from typing import Any, Optional

from dipeo.diagram_generated import ApiKeyID, LLMService, Message, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.conversation_manager import ConversationManager
from dipeo.domain.ports import ConversationRepository, PersonRepository

logger = logging.getLogger(__name__)


class ExecutionOrchestrator(ConversationManager):
    """Orchestrates person and conversation management during execution.
    
    This service coordinates between PersonRepository and ConversationRepository,
    ensuring proper wiring and interaction between persons and conversations.
    It implements ConversationManager for backward compatibility during migration.
    """
    
    def __init__(
        self,
        person_repository: PersonRepository,
        conversation_repository: ConversationRepository
    ):
        self._person_repo = person_repository
        self._conversation_repo = conversation_repository
        self._execution_logs: dict[str, list[dict[str, Any]]] = {}
        self._current_execution_id: Optional[str] = None
    
    # ===== Person Management =====
    
    def get_or_create_person(
        self,
        person_id: PersonID,
        name: Optional[str] = None,
        llm_config: Optional[PersonLLMConfig] = None
    ) -> Person:
        """Get existing person or create new one with proper wiring."""
        if self._person_repo.exists(person_id):
            person = self._person_repo.get(person_id)
        else:
            if not llm_config:
                # Default LLM config if not provided
                llm_config = PersonLLMConfig(
                    service=LLMService("openai"),
                    model="gpt-5-nano-2025-08-07",
                    api_key_id=ApiKeyID("default")
                )
            
            person = self._person_repo.create(
                person_id=person_id,
                name=name or str(person_id),
                llm_config=llm_config
            )
        
        # Wire up the conversation manager
        person._conversation_manager = self
        return person
    
    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Register a new person with the given configuration.
        
        This method exists for backward compatibility with existing code.
        """
        person_id_obj = PersonID(person_id)
        
        if not self._person_repo.exists(person_id_obj):
            api_key_id_value = config.get('api_key_id', 'default')
            llm_config = PersonLLMConfig(
                service=LLMService(config.get('service', 'openai')),
                model=config.get('model', 'gpt-5-nano-2025-08-07'),
                api_key_id=ApiKeyID(api_key_id_value),
                system_prompt=config.get('system_prompt', '')  # Include system_prompt from config
            )
            
            person = self._person_repo.create(
                person_id=person_id_obj,
                name=config.get('name', person_id),
                llm_config=llm_config
            )
            
            # Wire up the conversation manager
            person._conversation_manager = self
    
    def get_person(self, person_id: PersonID) -> Person:
        """Get a person by ID."""
        return self._person_repo.get(person_id)
    
    def get_all_persons(self) -> dict[PersonID, Person]:
        """Get all registered persons."""
        return self._person_repo.get_all()
    
    # ===== Conversation Management =====
    
    def get_conversation(self):
        """Get the global conversation shared by all persons."""
        return self._conversation_repo.get_global_conversation()
    
    def add_message(
        self,
        message: Message,
        execution_id: str,
        node_id: Optional[str] = None
    ) -> None:
        """Add a message to the global conversation and log it."""
        self._current_execution_id = execution_id
        
        # Add to global conversation
        self._conversation_repo.add_message(message)
        
        # Log for persistence/debugging
        if execution_id not in self._execution_logs:
            self._execution_logs[execution_id] = []
        
        self._execution_logs[execution_id].append({
            "role": self._get_role_from_message(message),
            "content": message.content,
            "from_person_id": str(message.from_person_id),
            "to_person_id": str(message.to_person_id),
            "node_id": node_id,
            "timestamp": message.timestamp
        })
    
    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        """Get conversation history from a person's perspective.
        
        This uses the person's memory filters to provide their view
        of the conversation.
        """
        person_id_obj = PersonID(person_id)
        
        if not self._person_repo.exists(person_id_obj):
            return []
        
        person = self._person_repo.get(person_id_obj)
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
        """Clear all conversations and reset person memories."""
        # Clear global conversation
        self._conversation_repo.clear()
        
        # Reset each person's memory configuration
        for _person_id, person in self._person_repo.get_all().items():
            person.set_memory_limit(-1)  # Remove limit
            person.set_memory_view(person.memory_view)  # Reset to default view
        
        # Clear execution logs
        self._execution_logs.clear()
        self._current_execution_id = None
    
    def clear_person_messages(self, person_id: PersonID) -> None:
        """Clear all messages involving a specific person from the conversation.
        
        This is used for GOLDFISH memory profile to ensure complete memory reset
        between diagram executions.
        """
        # Get current conversation
        conversation = self._conversation_repo.get_global_conversation()
        
        # Filter out messages involving this person
        filtered_messages = [
            msg for msg in conversation.messages
            if msg.from_person_id != person_id and msg.to_person_id != person_id
        ]
        
        # Clear and rebuild conversation with filtered messages
        conversation.clear()
        for msg in filtered_messages:
            conversation.add_message(msg)
        
        # Also clear from execution logs
        if self._current_execution_id and self._current_execution_id in self._execution_logs:
            self._execution_logs[self._current_execution_id] = [
                log for log in self._execution_logs[self._current_execution_id]
                if log.get("from_person_id") != str(person_id) and log.get("to_person_id") != str(person_id)
            ]
    
    # ===== Initialization =====
    
    async def initialize(self) -> None:
        """Initialize the orchestrator and wire up existing persons."""
        # Wire up any existing persons
        for person in self._person_repo.get_all().values():
            person._conversation_manager = self
    
    # ===== Helper Methods =====
    
    @staticmethod
    def _get_role_from_message(message: Message) -> str:
        """Determine the role of a message for logging."""
        if message.from_person_id == "system":
            return "system"
        elif message.from_person_id == message.to_person_id:
            return "assistant"
        else:
            return "user"
    
    def get_person_config(self, person_id: str) -> Optional[PersonLLMConfig]:
        """Get a person's LLM configuration.
        
        This method exists for backward compatibility.
        """
        person_id_obj = PersonID(person_id)
        if self._person_repo.exists(person_id_obj):
            person = self._person_repo.get(person_id_obj)
            return person.llm_config
        return None