"""Clean in-memory implementation of PersonRepository focusing on persistence only.

This implementation follows the repository pattern strictly by only handling
data persistence and retrieval, without any business logic or object construction.
"""

from dipeo.diagram_generated import LLMService, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.ports import PersonRepository


class CleanInMemoryPersonRepository(PersonRepository):
    """Clean in-memory implementation of PersonRepository.

    This implementation strictly follows the repository pattern by only
    handling persistence operations. Object construction and dependency
    wiring should be handled by factories or services.
    """

    def __init__(self):
        """Initialize empty person storage."""
        self._persons: dict[PersonID, Person] = {}

    def get(self, person_id: PersonID) -> Person:
        """Retrieve a person by ID.

        Args:
            person_id: The person's unique identifier

        Returns:
            The requested Person instance

        Raises:
            KeyError: If person not found
        """
        if person_id not in self._persons:
            raise KeyError(f"Person {person_id} not found")
        return self._persons[person_id]

    def save(self, person: Person) -> None:
        """Save or update a person.

        Args:
            person: The person to persist
        """
        self._persons[person.id] = person

    def create(
        self,
        person_id: PersonID,
        name: str,
        llm_config: PersonLLMConfig,
    ) -> Person:
        """Create and persist a new person.

        Note: This method creates a basic Person without cognitive components.
        Use PersonFactory for creating persons with brain components.

        Args:
            person_id: Unique identifier for the person
            name: Human-readable name
            llm_config: LLM configuration

        Returns:
            The created and persisted Person instance
        """
        person = Person(id=person_id, name=name, llm_config=llm_config)
        self.save(person)
        return person

    def delete(self, person_id: PersonID) -> None:
        """Delete a person by ID.

        Args:
            person_id: The person to delete
        """
        if person_id in self._persons:
            del self._persons[person_id]

    def exists(self, person_id: PersonID) -> bool:
        """Check if a person exists.

        Args:
            person_id: The person to check

        Returns:
            True if the person exists, False otherwise
        """
        return person_id in self._persons

    def get_all(self) -> dict[PersonID, Person]:
        """Get all persons.

        Returns:
            A copy of all persons keyed by their IDs
        """
        return self._persons.copy()

    def get_by_service(self, service: LLMService) -> list[Person]:
        """Get all persons using a specific LLM service.

        Args:
            service: The LLM service to filter by

        Returns:
            List of persons using the specified service
        """
        return [person for person in self._persons.values() if person.llm_config.service == service]

    def clear(self) -> None:
        """Clear all persons from storage."""
        self._persons.clear()

    def get_or_create(
        self,
        person_id: PersonID,
        name: str | None = None,
        llm_config: PersonLLMConfig | None = None,
    ) -> Person:
        """Get existing person or create new one.

        Note: This creates basic persons without cognitive components.
        Use PersonFactory for complete person creation.

        Args:
            person_id: The person identifier
            name: Optional name (defaults to person_id string)
            llm_config: Optional LLM configuration

        Returns:
            The retrieved or created Person instance
        """
        if self.exists(person_id):
            return self.get(person_id)

        # Apply minimal defaults
        if not name:
            name = str(person_id)

        if not llm_config:
            # Minimal default config - factory should handle proper defaults
            from dipeo.diagram_generated import ApiKeyID

            llm_config = PersonLLMConfig(
                service=LLMService("openai"),
                model="gpt-5-nano-2025-08-07",
                api_key_id=ApiKeyID("APIKEY_52609F"),
            )

        return self.create(person_id=person_id, name=name, llm_config=llm_config)

    def register_person(self, person_id: str, config: dict) -> None:
        """Register a new person with the given configuration.

        This method exists for backward compatibility. New code should
        use create() or get_or_create() directly.

        Args:
            person_id: String identifier for the person
            config: Dictionary with person configuration
        """
        from dipeo.diagram_generated import ApiKeyID

        person_id_obj = PersonID(person_id)

        if not self.exists(person_id_obj):
            llm_config = PersonLLMConfig(
                service=LLMService(config.get("service", "openai")),
                model=config.get("model", "gpt-5-nano-2025-08-07"),
                api_key_id=ApiKeyID(config.get("api_key_id", "APIKEY_52609F")),
                system_prompt=config.get("system_prompt", ""),
            )

            self.create(
                person_id=person_id_obj, name=config.get("name", person_id), llm_config=llm_config
            )
