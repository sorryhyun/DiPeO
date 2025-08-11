"""Protocol for managing person instances during diagram execution."""

from abc import abstractmethod
from typing import Protocol

from dipeo.diagram_generated import LLMService, PersonID, PersonLLMConfig

from .person import Person


class PersonManager(Protocol):
    
    @abstractmethod
    def get_person(self, person_id: PersonID) -> Person:
        ...
    
    @abstractmethod
    def create_person(
        self,
        person_id: PersonID,
        name: str,
        llm_config: PersonLLMConfig,
        role: str | None = None
    ) -> Person:
        ...
    
    @abstractmethod
    def update_person_config(
        self,
        person_id: PersonID,
        llm_config: PersonLLMConfig | None = None,
        role: str | None = None
    ) -> None:
        ...
    
    @abstractmethod
    def get_all_persons(self) -> dict[PersonID, Person]:
        ...
    
    @abstractmethod
    def get_persons_by_service(self, service: LLMService) -> list[Person]:
        ...
    
    @abstractmethod
    def remove_person(self, person_id: PersonID) -> None:
        ...
    
    @abstractmethod
    def clear_all_persons(self) -> None:
        ...
    
    @abstractmethod
    def person_exists(self, person_id: PersonID) -> bool:
        ...


