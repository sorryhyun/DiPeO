"""Person repository protocol - defines interface for person persistence."""

from typing import Protocol

from dipeo.diagram_generated import LLMService, PersonID, PersonLLMConfig

from ..conversation import Person


class PersonRepository(Protocol):
    """Repository protocol for managing Person entities.
    
    This defines the interface that infrastructure must implement
    for persisting and retrieving Person instances.
    """
    
    def get(self, person_id: PersonID) -> Person:
        """Retrieve a person by ID.
        
        Raises:
            KeyError: If person not found
        """
        ...
    
    def save(self, person: Person) -> None:
        """Save or update a person."""
        ...
    
    def create(
        self,
        person_id: PersonID,
        name: str,
        llm_config: PersonLLMConfig,
    ) -> Person:
        """Create a new person.
        
        Returns:
            The created Person instance
        """
        ...
    
    def delete(self, person_id: PersonID) -> None:
        """Delete a person by ID."""
        ...
    
    def exists(self, person_id: PersonID) -> bool:
        """Check if a person exists."""
        ...
    
    def get_all(self) -> dict[PersonID, Person]:
        """Get all persons."""
        ...
    
    def get_by_service(self, service: LLMService) -> list[Person]:
        """Get all persons using a specific LLM service."""
        ...
    
    def clear(self) -> None:
        """Clear all persons."""
        ...