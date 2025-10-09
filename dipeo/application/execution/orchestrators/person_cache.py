"""Person caching and lifecycle management."""

import logging
from typing import TYPE_CHECKING, Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import ApiKeyID, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.ports import PersonRepository

if TYPE_CHECKING:
    from dipeo.application.execution.use_cases.prompt_loading import PromptLoadingUseCase

logger = get_module_logger(__name__)


class PersonCache:
    """Manages person instances with caching and diagram-based initialization."""

    def __init__(
        self,
        person_repository: PersonRepository,
        prompt_loading_use_case: "PromptLoadingUseCase | None" = None,
    ):
        self._person_repo = person_repository
        self._prompt_loading_use_case = prompt_loading_use_case
        self._person_cache: dict[PersonID, Person] = {}

    def get_or_create_person(
        self,
        person_id: PersonID,
        name: str | None = None,
        llm_config: PersonLLMConfig | None = None,
        diagram: Any | None = None,
    ) -> Person:
        """Get cached person or create new one from repository/diagram."""
        if person_id in self._person_cache:
            return self._person_cache[person_id]

        if diagram and not self._person_repo.exists(person_id):
            person = self._create_person_from_diagram(person_id, diagram)
            if person:
                self._person_cache[person_id] = person
                return person

        person = self._person_repo.get_or_create(person_id, name, llm_config)
        self._person_cache[person_id] = person
        return person

    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Register a person with configuration."""
        self._person_repo.register_person(person_id, config)

    def get_person(self, person_id: PersonID) -> Person:
        """Get a person from the repository."""
        return self._person_repo.get(person_id)

    def get_all_persons(self) -> dict[PersonID, Person]:
        """Get all persons from the repository."""
        return self._person_repo.get_all()

    def get_person_config(self, person_id: str) -> PersonLLMConfig | None:
        """Get LLM configuration for a person."""
        person_id_obj = PersonID(person_id)
        if self._person_repo.exists(person_id_obj):
            person = self._person_repo.get(person_id_obj)
            return person.llm_config
        return None

    def register_diagram_persons(self, diagram: Any) -> None:
        """Register all persons from a diagram into the cache."""
        persons_catalog = None
        if hasattr(diagram, "metadata") and isinstance(diagram.metadata, dict):
            persons_catalog = diagram.metadata.get("persons", {})
        elif hasattr(diagram, "persons"):
            persons_catalog = {}
            persons_list = (
                list(diagram.persons.values())
                if isinstance(diagram.persons, dict)
                else diagram.persons
            )
            for person in persons_list:
                p_id = str(person.id) if hasattr(person, "id") else str(person.name)
                person_config_dict = {}
                if hasattr(person, "llm_config"):
                    llm_config = person.llm_config
                    service_value = (
                        llm_config.service if hasattr(llm_config, "service") else "openai"
                    )
                    if hasattr(service_value, "value"):
                        person_config_dict["service"] = service_value.value
                    else:
                        person_config_dict["service"] = str(service_value)
                    person_config_dict["model"] = (
                        str(llm_config.model)
                        if hasattr(llm_config, "model")
                        else "gpt-5-nano-2025-08-07"
                    )
                    person_config_dict["api_key_id"] = (
                        str(llm_config.api_key_id)
                        if hasattr(llm_config, "api_key_id")
                        else "default"
                    )
                    if hasattr(llm_config, "system_prompt") and llm_config.system_prompt:
                        person_config_dict["system_prompt"] = llm_config.system_prompt
                persons_catalog[p_id] = person_config_dict

        if not persons_catalog:
            return

        for person_id, _config in persons_catalog.items():
            person_id_obj = PersonID(person_id)
            if person_id_obj not in self._person_cache:
                person = self._create_person_from_diagram(person_id_obj, diagram)
                if person:
                    self._person_cache[person_id_obj] = person
                    logger.debug(f"Registered person from diagram: {person_id}")

    def _create_person_from_diagram(self, person_id: PersonID, diagram: Any) -> Person | None:
        """Create a person instance from diagram metadata."""
        persons_catalog = None
        if hasattr(diagram, "metadata") and isinstance(diagram.metadata, dict):
            persons_catalog = diagram.metadata.get("persons", {})
        elif hasattr(diagram, "persons"):
            persons_catalog = {}
            persons_list = (
                list(diagram.persons.values())
                if isinstance(diagram.persons, dict)
                else diagram.persons
            )
            for person in persons_list:
                p_id = str(person.id) if hasattr(person, "id") else str(person.name)
                person_config_dict = {}
                if hasattr(person, "llm_config"):
                    llm_config = person.llm_config
                    service_value = (
                        llm_config.service if hasattr(llm_config, "service") else "openai"
                    )
                    if hasattr(service_value, "value"):
                        person_config_dict["service"] = service_value.value
                    else:
                        person_config_dict["service"] = str(service_value)
                    person_config_dict["model"] = (
                        str(llm_config.model)
                        if hasattr(llm_config, "model")
                        else "gpt-5-nano-2025-08-07"
                    )
                    person_config_dict["api_key_id"] = (
                        str(llm_config.api_key_id)
                        if hasattr(llm_config, "api_key_id")
                        else "default"
                    )
                    if hasattr(llm_config, "system_prompt") and llm_config.system_prompt:
                        person_config_dict["system_prompt"] = llm_config.system_prompt
                persons_catalog[p_id] = person_config_dict

        if not persons_catalog:
            return None

        person_config = None
        for p_id, config in persons_catalog.items():
            if PersonID(p_id) == person_id:
                person_config = config
                break

        if not person_config:
            return None

        api_key_id = person_config.get("api_key_id")
        if not api_key_id:
            api_key_id = "APIKEY_52609F"
            logger.warning(f"No api_key_id for person {person_id}, defaulting to {api_key_id}")

        system_prompt = person_config.get("system_prompt")
        prompt_file = person_config.get("prompt_file")

        if prompt_file and self._prompt_loading_use_case:
            loaded_prompt = self._load_prompt(
                prompt_file=prompt_file,
                inline_prompt=None,
                diagram=diagram,
                node_label=f"Person {person_id}",
            )
            if loaded_prompt:
                system_prompt = loaded_prompt
                logger.debug(
                    f"Loaded system prompt from file '{prompt_file}' for person {person_id}"
                )

        llm_config = PersonLLMConfig(
            service=person_config.get("service", "openai"),
            model=person_config.get("model", "gpt-5-nano-2025-08-07"),
            api_key_id=ApiKeyID(api_key_id),
            system_prompt=system_prompt,
            prompt_file=None,
        )

        person = self._person_repo.get_or_create(
            person_id=person_id,
            name=person_config.get("name", str(person_id)),
            llm_config=llm_config,
        )

        return person

    def _load_prompt(
        self,
        prompt_file: str | None = None,
        inline_prompt: str | None = None,
        diagram: Any | None = None,
        node_label: str | None = None,
    ) -> str | None:
        """Load prompt using the prompt loading use case."""
        if not self._prompt_loading_use_case:
            logger.warning("PromptLoadingUseCase not configured, using inline prompt only")
            return inline_prompt

        diagram_source_path = None
        if diagram:
            diagram_source_path = self._prompt_loading_use_case.get_diagram_source_path(diagram)

        return self._prompt_loading_use_case.load_prompt(
            prompt_file=prompt_file,
            inline_prompt=inline_prompt,
            diagram_source_path=diagram_source_path,
            node_label=node_label,
        )
