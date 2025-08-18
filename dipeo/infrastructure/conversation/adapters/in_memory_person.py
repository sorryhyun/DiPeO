"""In-memory implementation of PersonRepository."""

from dipeo.diagram_generated import LLMService, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.ports import PersonRepository


class InMemoryPersonRepository(PersonRepository):
    """In-memory implementation of PersonRepository.
    
    This implementation stores persons in memory during execution.
    It does not persist data between executions.
    """
    
    def __init__(self):
        self._persons: dict[PersonID, Person] = {}
    
    def get(self, person_id: PersonID) -> Person:
        """Retrieve a person by ID.
        
        Raises:
            KeyError: If person not found
        """
        if person_id not in self._persons:
            raise KeyError(f"Person {person_id} not found")
        return self._persons[person_id]
    
    def save(self, person: Person) -> None:
        """Save or update a person."""
        self._persons[person.id] = person
    
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
        person = Person(
            id=person_id,
            name=name,
            llm_config=llm_config,
            conversation_manager=None  # Will be set by orchestrator
        )
        self.save(person)
        return person
    
    def delete(self, person_id: PersonID) -> None:
        """Delete a person by ID."""
        if person_id in self._persons:
            del self._persons[person_id]
    
    def exists(self, person_id: PersonID) -> bool:
        """Check if a person exists."""
        return person_id in self._persons
    
    def get_all(self) -> dict[PersonID, Person]:
        """Get all persons."""
        return self._persons.copy()
    
    def get_by_service(self, service: LLMService) -> list[Person]:
        """Get all persons using a specific LLM service."""
        return [
            person for person in self._persons.values()
            if person.llm_config.service == service
        ]
    
    def clear(self) -> None:
        """Clear all persons."""
        self._persons.clear()