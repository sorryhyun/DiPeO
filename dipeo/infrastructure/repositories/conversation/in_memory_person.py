"""In-memory implementation of PersonRepository."""

from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated import ApiKeyID, LLMService, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.ports import PersonRepository

if TYPE_CHECKING:
    from dipeo.application.execution.orchestrators.execution_orchestrator import (
        ExecutionOrchestrator,
    )


class InMemoryPersonRepository(PersonRepository):
    """In-memory implementation of PersonRepository.

    This implementation stores persons in memory during execution.
    It does not persist data between executions.
    """

    def __init__(self):
        self._persons: dict[PersonID, Person] = {}
        self._orchestrator: ExecutionOrchestrator | None = None

    def set_orchestrator(self, orchestrator: "ExecutionOrchestrator") -> None:
        """Set the orchestrator for wiring brain components.

        This is called after construction to avoid circular dependencies.
        """
        self._orchestrator = orchestrator

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
        """Create a new person with brain component wired up.

        Returns:
            The created Person instance with cognitive components
        """
        person = Person(id=person_id, name=name, llm_config=llm_config)

        # Wire up brain component if orchestrator is available
        if self._orchestrator:
            from dipeo.domain.conversation.brain import CognitiveBrain
            from dipeo.infrastructure.llm.adapters import LLMMemorySelectionAdapter

            # Create memory selector implementation
            memory_selector = LLMMemorySelectionAdapter(self._orchestrator)

            # Wire brain with memory selector
            person.brain = CognitiveBrain(memory_selector=memory_selector)

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
        return [person for person in self._persons.values() if person.llm_config.service == service]

    def clear(self) -> None:
        """Clear all persons."""
        self._persons.clear()

    def get_or_create(
        self,
        person_id: PersonID,
        name: str | None = None,
        llm_config: PersonLLMConfig | None = None,
    ) -> Person:
        """Get existing person or create new one with defaults.

        Args:
            person_id: The person identifier
            name: Optional name (defaults to person_id string)
            llm_config: Optional LLM configuration (defaults to gpt-5-nano)

        Returns:
            The retrieved or created Person instance
        """
        if self.exists(person_id):
            return self.get(person_id)

        # Create with defaults if not provided
        if not llm_config:
            # Default to APIKEY_52609F which is the most common API key in diagrams
            llm_config = PersonLLMConfig(
                service=LLMService("openai"),
                model="gpt-5-nano-2025-08-07",
                api_key_id=ApiKeyID("APIKEY_52609F"),
            )

        return self.create(person_id=person_id, name=name or str(person_id), llm_config=llm_config)

    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Register a new person with the given configuration.

        This method exists for backward compatibility with existing code.

        Args:
            person_id: String identifier for the person
            config: Dictionary with 'name', 'service', 'model', 'api_key_id', 'system_prompt'
        """
        person_id_obj = PersonID(person_id)

        if not self.exists(person_id_obj):
            # Default to APIKEY_52609F which is the most common API key in diagrams
            api_key_id_value = config.get("api_key_id", "APIKEY_52609F")
            llm_config = PersonLLMConfig(
                service=LLMService(config.get("service", "openai")),
                model=config.get("model", "gpt-5-nano-2025-08-07"),
                api_key_id=ApiKeyID(api_key_id_value),
                system_prompt=config.get("system_prompt", ""),
            )

            self.create(
                person_id=person_id_obj, name=config.get("name", person_id), llm_config=llm_config
            )
