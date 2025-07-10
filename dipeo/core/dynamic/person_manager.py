"""Protocol for managing person instances during diagram execution."""

from typing import Protocol, Dict, List, Optional
from abc import abstractmethod
from dipeo.models import PersonID, LLMService, PersonLLMConfig
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
        role: Optional[str] = None
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
        llm_config: Optional[PersonLLMConfig] = None,
        role: Optional[str] = None
    ) -> None:
        """Update a person's configuration.
        
        Args:
            person_id: The ID of the person to update
            llm_config: New LLM configuration (if provided)
            role: New role description (if provided)
        """
        ...
    
    @abstractmethod
    def get_all_persons(self) -> Dict[PersonID, Person]:
        """Get all active person instances.
        
        Returns:
            Dictionary mapping person_id to Person objects
        """
        ...
    
    @abstractmethod
    def get_persons_by_service(self, service: LLMService) -> List[Person]:
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


class PersonPersistence(Protocol):
    """Protocol for persisting person configurations."""
    
    @abstractmethod
    async def save_persons(
        self,
        execution_id: str,
        persons: Dict[PersonID, Person]
    ) -> str:
        """Save all person configurations from an execution.
        
        Args:
            execution_id: The execution ID
            persons: Map of person_id to Person objects
            
        Returns:
            Path or identifier where persons were saved
        """
        ...
    
    @abstractmethod
    async def load_persons(
        self,
        execution_id: str
    ) -> Dict[PersonID, Person]:
        """Load person configurations from a previous execution.
        
        Args:
            execution_id: The execution ID to load
            
        Returns:
            Map of person_id to Person objects
        """
        ...
    
    @abstractmethod
    async def export_person_config(
        self,
        person: Person,
        format: str = "json"
    ) -> str:
        """Export a person's configuration.
        
        Args:
            person: The person to export
            format: Export format (json, yaml, etc.)
            
        Returns:
            Serialized configuration string
        """
        ...