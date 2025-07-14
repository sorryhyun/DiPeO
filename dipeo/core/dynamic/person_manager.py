"""Protocol for managing person instances during diagram execution."""

from abc import abstractmethod
from typing import Protocol

from dipeo.models import LLMService, PersonID, PersonLLMConfig

from .person import Person


class PersonManager(Protocol):
    """Manages person instances and their configurations during execution."""
    
    @abstractmethod
    def get_person(self, person_id: PersonID) -> Person:
        """Get a person instance by ID.
        
        Args:
            person_id: The ID of the person
            
        Returns:
            Person object with configuration and state
            
        Raises:
            KeyError: If person not found
        """
        ...
    
    @abstractmethod
    def create_person(
        self,
        person_id: PersonID,
        name: str,
        llm_config: PersonLLMConfig,
        role: str | None = None
    ) -> Person:
        """Create a new person instance.
        
        Args:
            person_id: Unique identifier for the person
            name: Display name
            llm_config: LLM configuration for this person
            role: Optional role description
            
        Returns:
            New Person object
        """
        ...
    
    @abstractmethod
    def update_person_config(
        self,
        person_id: PersonID,
        llm_config: PersonLLMConfig | None = None,
        role: str | None = None
    ) -> None:
        """Update a person's configuration.
        
        Args:
            person_id: The ID of the person to update
            llm_config: New LLM configuration (if provided)
            role: New role description (if provided)
        """
        ...
    
    @abstractmethod
    def get_all_persons(self) -> dict[PersonID, Person]:
        """Get all active person instances.
        
        Returns:
            Dictionary mapping person_id to Person objects
        """
        ...
    
    @abstractmethod
    def get_persons_by_service(self, service: LLMService) -> list[Person]:
        """Get all persons using a specific LLM service.
        
        Args:
            service: The LLM service to filter by
            
        Returns:
            List of Person objects using the specified service
        """
        ...
    
    @abstractmethod
    def remove_person(self, person_id: PersonID) -> None:
        """Remove a person from the manager.
        
        Args:
            person_id: The ID of the person to remove
        """
        ...
    
    @abstractmethod
    def clear_all_persons(self) -> None:
        """Remove all persons from the manager."""
        ...
    
    @abstractmethod
    def person_exists(self, person_id: PersonID) -> bool:
        """Check if a person exists.
        
        Args:
            person_id: The ID to check
            
        Returns:
            True if person exists, False otherwise
        """
        ...


