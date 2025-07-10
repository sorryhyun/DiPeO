"""Protocol for managing conversation flow and memory during execution."""

from typing import Protocol, List, Dict, Any, Optional
from abc import abstractmethod
from dipeo.models import Message, ConversationMetadata, ForgettingMode
from .conversation import Conversation


class ConversationManager(Protocol):
    """Manages conversation state and memory during diagram execution."""
    
    @abstractmethod
    def get_conversation(self, person_id: str) -> Conversation:
        """Get the conversation for a specific person.
        
        Args:
            person_id: The ID of the person
            
        Returns:
            Conversation object with messages, context, and metadata
        """
        ...
    
    @abstractmethod
    def create_conversation(self, person_id: str) -> Conversation:
        """Create a new conversation for a person.
        
        Args:
            person_id: The ID of the person
            
        Returns:
            New Conversation object
        """
        ...
    
    @abstractmethod
    def add_message(
        self,
        person_id: str,
        message: Message,
        execution_id: str,
        node_id: Optional[str] = None
    ) -> None:
        """Add a message to a person's conversation.
        
        Args:
            person_id: The ID of the person
            message: The message to add
            execution_id: The current execution ID
            node_id: Optional ID of the node that generated this message
        """
        ...
    
    @abstractmethod
    def apply_forgetting(
        self,
        person_id: str,
        mode: ForgettingMode,
        execution_id: Optional[str] = None
    ) -> int:
        """Apply a forgetting strategy to a person's conversation.
        
        Args:
            person_id: The ID of the person
            mode: The forgetting mode to apply
            execution_id: Optional execution ID to scope the forgetting
            
        Returns:
            Number of messages forgotten
        """
        ...
    
    @abstractmethod
    def merge_conversations(
        self,
        source_person_id: str,
        target_person_id: str
    ) -> None:
        """Merge one person's conversation into another's.
        
        Args:
            source_person_id: The person whose messages to copy
            target_person_id: The person to receive the messages
        """
        ...
    
    @abstractmethod
    def clear_conversation(
        self,
        person_id: str,
        execution_id: Optional[str] = None
    ) -> None:
        """Clear a person's conversation history.
        
        Args:
            person_id: The ID of the person
            execution_id: Optional execution ID to scope the clearing
        """
        ...
    
    @abstractmethod
    def get_all_conversations(self) -> Dict[str, Conversation]:
        """Get all active conversations.
        
        Returns:
            Dictionary mapping person_id to Conversation objects
        """
        ...


class ConversationPersistence(Protocol):
    """Protocol for persisting conversation state."""
    
    @abstractmethod
    async def save_conversations(
        self,
        execution_id: str,
        conversations: Dict[str, Conversation]
    ) -> str:
        """Save all conversations from an execution.
        
        Args:
            execution_id: The execution ID
            conversations: Map of person_id to Conversation objects
            
        Returns:
            Path or identifier where conversations were saved
        """
        ...
    
    @abstractmethod
    async def load_conversations(
        self,
        execution_id: str
    ) -> Dict[str, Conversation]:
        """Load conversations from a previous execution.
        
        Args:
            execution_id: The execution ID to load
            
        Returns:
            Map of person_id to Conversation objects
        """
        ...
    
    @abstractmethod
    async def list_conversations(
        self,
        limit: Optional[int] = None
    ) -> List[ConversationMetadata]:
        """List available conversation records.
        
        Args:
            limit: Optional limit on number of records
            
        Returns:
            List of conversation metadata
        """
        ...