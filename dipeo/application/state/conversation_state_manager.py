"""Tracks conversation state between persons during diagram execution."""

from typing import Any, Dict, List, Optional, Set
import logging
from collections import defaultdict

from dipeo.core.dynamic import Person
from dipeo.models import Message, PersonID

logger = logging.getLogger(__name__)


class ConversationStateManager:
    """Tracks conversation state between persons in the diagram.
    
    This class manages the dynamic conversation state for all Person nodes
    during diagram execution. It maintains a registry of active persons,
    tracks global context that can be shared between persons, and provides
    utilities for managing multi-agent conversations.
    """
    
    def __init__(self):
        self.persons: Dict[str, Person] = {}
        self.global_context: Dict[str, Any] = {}
        self.conversation_history: List[Message] = []
        self.person_message_counts: Dict[str, int] = defaultdict(int)
        self.active_conversations: Set[str] = set()
    
    def update_person_conversation(self, person_id: str, message: Message) -> None:
        """Update a person's conversation with a new message.
        
        This method adds a message to a person's conversation history and
        updates tracking information.
        
        Args:
            person_id: The ID of the person whose conversation to update
            message: The message to add to the conversation
        """
        person = self.persons.get(person_id)
        if person:
            person.add_message(message)
            self.conversation_history.append(message)
            self.person_message_counts[person_id] += 1
            
            # Track active conversations
            if message.from_person_id != "system":
                conversation_key = self._get_conversation_key(
                    str(message.from_person_id), 
                    str(message.to_person_id)
                )
                self.active_conversations.add(conversation_key)
            
            logger.debug(f"Updated conversation for person {person_id} with message from {message.from_person_id}")
        else:
            logger.warning(f"Attempted to update conversation for unknown person: {person_id}")
    
    def register_person(self, person: Person) -> None:
        """Register a new person in the conversation state.
        
        Args:
            person: The Person instance to register
        """
        self.persons[str(person.id)] = person
        logger.info(f"Registered person: {person.id} ({person.name})")
    
    def unregister_person(self, person_id: str) -> None:
        """Remove a person from the conversation state.
        
        Args:
            person_id: The ID of the person to remove
        """
        if person_id in self.persons:
            del self.persons[person_id]
            logger.info(f"Unregistered person: {person_id}")
    
    def get_person(self, person_id: str) -> Optional[Person]:
        """Get a person by their ID.
        
        Args:
            person_id: The ID of the person to retrieve
            
        Returns:
            The Person instance if found, None otherwise
        """
        return self.persons.get(person_id)
    
    def get_all_persons(self) -> List[Person]:
        """Get all registered persons.
        
        Returns:
            List of all Person instances
        """
        return list(self.persons.values())
    
    def update_global_context(self, updates: Dict[str, Any]) -> None:
        """Update the global context with new values.
        
        Global context can be used to share information between persons
        that don't directly communicate.
        
        Args:
            updates: Dictionary of context updates to merge
        """
        self.global_context.update(updates)
        logger.debug(f"Updated global context with {len(updates)} values")
    
    def get_global_context(self) -> Dict[str, Any]:
        """Get the current global context.
        
        Returns:
            Copy of the global context dictionary
        """
        return self.global_context.copy()
    
    def get_conversation_between(self, person1_id: str, person2_id: str) -> List[Message]:
        """Get all messages exchanged between two persons.
        
        Args:
            person1_id: ID of the first person
            person2_id: ID of the second person
            
        Returns:
            List of messages between the two persons
        """
        messages = []
        for msg in self.conversation_history:
            if ((str(msg.from_person_id) == person1_id and str(msg.to_person_id) == person2_id) or
                (str(msg.from_person_id) == person2_id and str(msg.to_person_id) == person1_id)):
                messages.append(msg)
        return messages
    
    def get_person_statistics(self, person_id: str) -> Dict[str, Any]:
        """Get conversation statistics for a person.
        
        Args:
            person_id: The ID of the person
            
        Returns:
            Dictionary containing conversation statistics
        """
        person = self.persons.get(person_id)
        if not person:
            return {}
        
        sent_messages = [
            msg for msg in self.conversation_history 
            if str(msg.from_person_id) == person_id
        ]
        received_messages = [
            msg for msg in self.conversation_history 
            if str(msg.to_person_id) == person_id
        ]
        
        return {
            "person_id": person_id,
            "person_name": person.name,
            "total_messages": self.person_message_counts[person_id],
            "sent_count": len(sent_messages),
            "received_count": len(received_messages),
            "conversation_partners": self._get_conversation_partners(person_id),
            "llm_config": {
                "service": person.llm_config.service,
                "model": person.llm_config.model
            }
        }
    
    def _get_conversation_partners(self, person_id: str) -> List[str]:
        """Get list of persons this person has conversed with.
        
        Args:
            person_id: The ID of the person
            
        Returns:
            List of person IDs
        """
        partners = set()
        for msg in self.conversation_history:
            if str(msg.from_person_id) == person_id and msg.to_person_id != "system":
                partners.add(str(msg.to_person_id))
            elif str(msg.to_person_id) == person_id and msg.from_person_id != "system":
                partners.add(str(msg.from_person_id))
        return list(partners)
    
    def _get_conversation_key(self, person1_id: str, person2_id: str) -> str:
        """Generate a unique key for a conversation between two persons.
        
        Args:
            person1_id: ID of the first person
            person2_id: ID of the second person
            
        Returns:
            Unique conversation key
        """
        # Sort IDs to ensure consistent key regardless of order
        ids = sorted([person1_id, person2_id])
        return f"{ids[0]}<->{ids[1]}"
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation state.
        
        Returns:
            Dictionary containing state summary
        """
        return {
            "person_count": len(self.persons),
            "total_messages": len(self.conversation_history),
            "active_conversations": len(self.active_conversations),
            "global_context_keys": list(self.global_context.keys()),
            "persons": {
                person_id: {
                    "name": person.name,
                    "message_count": self.person_message_counts[person_id]
                }
                for person_id, person in self.persons.items()
            }
        }
    
    def reset(self) -> None:
        """Reset the conversation state for a new execution."""
        self.persons.clear()
        self.global_context.clear()
        self.conversation_history.clear()
        self.person_message_counts.clear()
        self.active_conversations.clear()
        logger.debug("Conversation state reset")
    
    def __repr__(self) -> str:
        """String representation of the ConversationStateManager."""
        return (f"ConversationStateManager(persons={len(self.persons)}, "
                f"messages={len(self.conversation_history)}, "
                f"active_conversations={len(self.active_conversations)})")