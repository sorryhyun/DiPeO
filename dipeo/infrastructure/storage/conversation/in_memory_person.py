"""In-memory implementation of PersonRepository."""

from typing import Any, Optional

from dipeo.diagram_generated import ApiKeyID, LLMService, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.ports import PersonRepository


class InMemoryPersonRepository(PersonRepository):
    """In-memory PersonRepository that doesn't persist between executions."""

    def __init__(self, llm_service: Optional[Any] = None):
        """Initialize repository with optional LLM service.

        Args:
            llm_service: Optional LLM service for memory strategy
        """
        self._persons: dict[PersonID, Person] = {}
        self._llm_service = llm_service

    def set_llm_service(self, llm_service: Any) -> None:
        """Set LLM service for memory strategy creation.

        Args:
            llm_service: LLM service instance
        """
        self._llm_service = llm_service

    def get(self, person_id: PersonID) -> Person:
        if person_id not in self._persons:
            raise KeyError(f"Person {person_id} not found")
        return self._persons[person_id]

    def save(self, person: Person) -> None:
        self._persons[person.id] = person

    def create(
        self,
        person_id: PersonID,
        name: str,
        llm_config: PersonLLMConfig,
    ) -> Person:
        """Create person with memory strategy configured."""
        from dipeo.domain.conversation.memory_strategies import IntelligentMemoryStrategy

        # Create memory strategy with LLM service if available
        memory_strategy = None
        if self._llm_service:
            memory_strategy = IntelligentMemoryStrategy(
                llm_service=self._llm_service, person_repository=self
            )

        # If no memory strategy created, use IntelligentMemoryStrategy without LLM service
        # It will handle this gracefully by returning None when needed
        if not memory_strategy:
            memory_strategy = IntelligentMemoryStrategy()

        person = Person(
            id=person_id,
            name=name,
            llm_config=llm_config,
            memory_strategy=memory_strategy,
        )

        self.save(person)
        return person

    def delete(self, person_id: PersonID) -> None:
        if person_id in self._persons:
            del self._persons[person_id]

    def exists(self, person_id: PersonID) -> bool:
        return person_id in self._persons

    def get_all(self) -> dict[PersonID, Person]:
        return self._persons.copy()

    def get_by_service(self, service: LLMService) -> list[Person]:
        return [person for person in self._persons.values() if person.llm_config.service == service]

    def clear(self) -> None:
        self._persons.clear()

    def get_or_create(
        self,
        person_id: PersonID,
        name: str | None = None,
        llm_config: PersonLLMConfig | None = None,
    ) -> Person:
        if self.exists(person_id):
            return self.get(person_id)

        if not llm_config:
            llm_config = PersonLLMConfig(
                service=LLMService("openai"),
                model="gpt-5-nano-2025-08-07",
                api_key_id=ApiKeyID("APIKEY_52609F"),
            )

        return self.create(person_id=person_id, name=name or str(person_id), llm_config=llm_config)

    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Backward compatibility method for person registration."""
        person_id_obj = PersonID(person_id)

        if not self.exists(person_id_obj):
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
