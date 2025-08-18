"""Use case for updating person memory and memory filters."""

from typing import Optional, Any

from dipeo.domain.conversation import Person, PersonManager, MemoryView
from dipeo.domain.ports.person_repository import PersonRepository


class UpdateMemoryUseCase:
    """Use case for updating person memory configuration.
    
    This use case handles:
    - Updating person memory filters
    - Managing memory views
    - Configuring memory profiles
    """
    
    def __init__(
        self,
        person_repository: PersonRepository,
        person_manager: PersonManager
    ):
        """Initialize the use case with required dependencies.
        
        Args:
            person_repository: Repository for persisting person state
            person_manager: Domain service for person management
        """
        self.person_repository = person_repository
        self.person_manager = person_manager
    
    def update_memory_view(self, person_name: str, memory_view: MemoryView) -> None:
        """Update a person's memory view configuration.
        
        Args:
            person_name: Name of the person to update
            memory_view: New memory view setting
        """
        person = self.person_repository.get_person(person_name)
        if person:
            person.memory_filter.memory_view = memory_view
            # Note: In-memory repository updates are immediate
    
    def update_memory_profile(self, person_name: str, profile_name: str) -> None:
        """Apply a predefined memory profile to a person.
        
        Args:
            person_name: Name of the person to update
            profile_name: Name of the memory profile to apply
        """
        from dipeo.domain.conversation.memory_filters import MemoryProfiles
        
        person = self.person_repository.get_person(person_name)
        if person and hasattr(MemoryProfiles, profile_name.upper()):
            profile = getattr(MemoryProfiles, profile_name.upper())
            person.memory_filter = profile
    
    def update_memory_settings(
        self,
        person_name: str,
        max_messages: Optional[int] = None,
        memory_view: Optional[MemoryView] = None,
        max_words: Optional[int] = None
    ) -> None:
        """Update multiple memory settings for a person.
        
        Args:
            person_name: Name of the person to update
            max_messages: Maximum number of messages to remember
            memory_view: Memory view setting
            max_words: Maximum word count for memory
        """
        person = self.person_repository.get_person(person_name)
        if not person:
            return
        
        if max_messages is not None:
            person.memory_filter.max_messages = max_messages
        
        if memory_view is not None:
            person.memory_filter.memory_view = memory_view
        
        if max_words is not None:
            person.memory_filter.max_words = max_words
    
    def get_memory_configuration(self, person_name: str) -> Optional[dict[str, Any]]:
        """Get the current memory configuration for a person.
        
        Args:
            person_name: Name of the person
            
        Returns:
            Dictionary with memory configuration or None if person not found
        """
        person = self.person_repository.get_person(person_name)
        if not person:
            return None
        
        return {
            "memory_view": person.memory_filter.memory_view,
            "max_messages": person.memory_filter.max_messages,
            "max_words": person.memory_filter.max_words,
            "include_system_prompts": person.memory_filter.include_system_prompts,
            "only_from_persons": person.memory_filter.only_from_persons,
            "exclude_persons": person.memory_filter.exclude_persons
        }
    
    def reset_memory_to_default(self, person_name: str) -> None:
        """Reset a person's memory configuration to default settings.
        
        Args:
            person_name: Name of the person to reset
        """
        from dipeo.domain.conversation.memory_filters import MemoryProfiles
        
        person = self.person_repository.get_person(person_name)
        if person:
            person.memory_filter = MemoryProfiles.NORMAL