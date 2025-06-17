"""Interface for memory service."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path


class IMemoryService(ABC):
    """Interface for managing person memory and conversations."""
    
    @abstractmethod
    def get_or_create_person_memory(self, person_id: str) -> Any:
        """Get or create memory for a person."""
        pass
    
    @abstractmethod
    def add_message_to_conversation(self,
                                  person_id: str,
                                  execution_id: str,
                                  role: str,
                                  content: str,
                                  current_person_id: str,
                                  node_id: Optional[str] = None,
                                  timestamp: Optional[float] = None) -> None:
        """Add a message to a person's conversation."""
        pass
    
    @abstractmethod
    def forget_for_person(self, person_id: str, execution_id: Optional[str] = None) -> None:
        """Forget messages for a person."""
        pass
    
    @abstractmethod
    def forget_own_messages_for_person(self, person_id: str, execution_id: Optional[str] = None) -> None:
        """Forget own messages for a person."""
        pass
    
    @abstractmethod
    def get_conversation_history(self, person_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a person."""
        pass
    
    @abstractmethod
    async def save_conversation_log(self, execution_id: str, log_dir: Path) -> str:
        """Save conversation log to disk."""
        pass