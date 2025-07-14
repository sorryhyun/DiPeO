"""Simple in-memory implementation of PersonManager protocol."""


from dipeo.core.dynamic.person import Person
from dipeo.core.dynamic.person_manager import PersonManager
from dipeo.models import LLMService, PersonID, PersonLLMConfig


class PersonManagerImpl(PersonManager):
    """Simple in-memory implementation of PersonManager."""
    
    def __init__(self):
        self._persons: dict[PersonID, Person] = {}
    
    def get_person(self, person_id: PersonID) -> Person:
        if person_id not in self._persons:
            raise KeyError(f"Person {person_id} not found")
        return self._persons[person_id]
    
    def create_person(
        self,
        person_id: PersonID,
        name: str,
        llm_config: PersonLLMConfig,
        role: str | None = None
    ) -> Person:
        person = Person(
            id=person_id, 
            name=name, 
            llm_config=llm_config,
            conversation_manager=None  # Will be set during execution
        )
        self._persons[person_id] = person
        return person
    
    def update_person_config(
        self,
        person_id: PersonID,
        llm_config: PersonLLMConfig | None = None,
        role: str | None = None
    ) -> None:
        person = self.get_person(person_id)
        if llm_config:
            person.llm_config = llm_config
    
    def get_all_persons(self) -> dict[PersonID, Person]:
        return self._persons.copy()
    
    def get_persons_by_service(self, service: LLMService) -> list[Person]:
        return [
            person for person in self._persons.values()
            if person.llm_config.service == service
        ]
    
    def remove_person(self, person_id: PersonID) -> None:
        if person_id in self._persons:
            del self._persons[person_id]
    
    def clear_all_persons(self) -> None:
        self._persons.clear()
    
    def person_exists(self, person_id: PersonID) -> bool:
        return person_id in self._persons