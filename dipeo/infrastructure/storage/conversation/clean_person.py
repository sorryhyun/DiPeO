"""Clean in-memory implementation of PersonRepository focusing on persistence only.

This implementation follows the repository pattern strictly by only handling
data persistence and retrieval, without any business logic or object construction.
"""

from dipeo.diagram_generated import LLMService, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.ports import PersonRepository


class CleanInMemoryPersonRepository(PersonRepository):
    """Clean in-memory PersonRepository following strict repository pattern."""

    def __init__(self):
        self._persons: dict[PersonID, Person] = {}

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
        """Create basic Person without cognitive components. Use PersonFactory for complete persons."""
        person = Person(id=person_id, name=name, llm_config=llm_config)
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
        """Get existing or create basic person. Use PersonFactory for complete persons."""
        if self.exists(person_id):
            return self.get(person_id)

        if not name:
            name = str(person_id)

        if not llm_config:
            from dipeo.diagram_generated import ApiKeyID

            llm_config = PersonLLMConfig(
                service=LLMService("openai"),
                model="gpt-5-nano-2025-08-07",
                api_key_id=ApiKeyID("APIKEY_52609F"),
            )

        return self.create(person_id=person_id, name=name, llm_config=llm_config)

    def register_person(self, person_id: str, config: dict) -> None:
        """Register person. Backward compatibility method - use create() or get_or_create() instead."""
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
