"""Execution orchestrator that coordinates repositories during diagram execution."""

import logging
from typing import Any, Optional

from dipeo.diagram_generated import ApiKeyID, LLMService, Message, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Conversation, Person
from dipeo.domain.conversation.ports import ConversationRepository, PersonRepository

logger = logging.getLogger(__name__)


class ExecutionOrchestrator:
    """Orchestrates person and conversation management during execution.
    
    This service coordinates between PersonRepository and ConversationRepository,
    ensuring proper wiring and interaction between persons and conversations.
    """
    
    def __init__(
        self,
        person_repository: PersonRepository,
        conversation_repository: ConversationRepository
    ):
        self._person_repo = person_repository
        self._conversation_repo = conversation_repository
        self._execution_logs: dict[str, list[dict[str, Any]]] = {}
        
        # Wire orchestrator back to repository for brain/hand components
        if hasattr(self._person_repo, 'set_orchestrator'):
            self._person_repo.set_orchestrator(self)
        self._current_execution_id: Optional[str] = None
    
    # ===== Person Management =====
    
    def get_or_create_person(
        self,
        person_id: PersonID,
        name: Optional[str] = None,
        llm_config: Optional[PersonLLMConfig] = None
    ) -> Person:
        """Get existing person or create new one."""
        return self._person_repo.get_or_create(person_id, name, llm_config)
    
    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Register a new person with the given configuration.
        
        This method exists for backward compatibility with existing code.
        """
        self._person_repo.register_person(person_id, config)
    
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
        
        # Add to global conversation with metadata
        self._conversation_repo.add_message(message, execution_id, node_id)
        
        # Log for persistence/debugging (kept for backward compatibility)
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
        
        # Use repository's conversation history method
        history = self._conversation_repo.get_conversation_history(person_id_obj)
        
        # Add execution context if available
        if self._current_execution_id:
            for entry in history:
                entry["execution_id"] = self._current_execution_id
        
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
        # Delegate to repository
        self._conversation_repo.clear_person_messages(person_id)
        
        # Also clear from execution logs (kept for backward compatibility)
        if self._current_execution_id and self._current_execution_id in self._execution_logs:
            self._execution_logs[self._current_execution_id] = [
                log for log in self._execution_logs[self._current_execution_id]
                if log.get("from_person_id") != str(person_id) and log.get("to_person_id") != str(person_id)
            ]
    
    # ===== Initialization =====
    
    async def initialize(self) -> None:
        """Initialize the orchestrator."""
        # No need to wire up persons anymore
        pass
    
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
