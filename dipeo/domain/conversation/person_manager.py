"""Protocol for managing person instances during diagram execution."""

from abc import abstractmethod
from typing import Any, Optional, Protocol

from dipeo.diagram_generated import PersonID, PersonLLMConfig

from .person import Person


class PersonManager(Protocol):
    """Protocol for person management during execution.
    
    This protocol defines the minimal interface needed for managing persons
    during diagram execution. It focuses on retrieval and creation without
    direct manipulation, as persons are managed through repositories.
    """
    
    @abstractmethod
    def get_or_create_person(
        self,
        person_id: PersonID,
        name: Optional[str] = None,
        llm_config: Optional[PersonLLMConfig] = None
    ) -> Person:
        """Get existing person or create new one with proper wiring."""
        ...
    
    @abstractmethod
    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Register a new person with the given configuration.
        
        This method exists for backward compatibility with existing code.
        """
        ...
    
    @abstractmethod
    def get_person(self, person_id: PersonID) -> Person:
        """Get a person by ID."""
        ...
    
    @abstractmethod
    def get_all_persons(self) -> dict[PersonID, Person]:
        """Get all registered persons."""
        ...


