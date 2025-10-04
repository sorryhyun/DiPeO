"""Execution orchestrator that coordinates repositories during diagram execution."""

import logging
from typing import TYPE_CHECKING, Any, Optional

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import ApiKeyID, Message, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.ports import ConversationRepository, PersonRepository

if TYPE_CHECKING:
    from dipeo.application.execution.use_cases.prompt_loading import PromptLoadingUseCase
    from dipeo.domain.integrations.ports import LLMService as LLMServicePort

logger = get_module_logger(__name__)


class ExecutionOrchestrator:
    """Orchestrates person and conversation management during execution."""

    def __init__(
        self,
        person_repository: PersonRepository,
        conversation_repository: ConversationRepository | None = None,
        prompt_loading_use_case: Optional["PromptLoadingUseCase"] = None,
        memory_selector: Any = None,  # No longer using domain adapters
        llm_service: Optional["LLMServicePort"] = None,
    ):
        self._person_repo = person_repository
        self._conversation_repo = conversation_repository
        self._prompt_loading_use_case = prompt_loading_use_case
        self._memory_selector = memory_selector
        self._llm_service = llm_service
        self._execution_logs: dict[str, list[dict[str, Any]]] = {}

        self._person_cache: dict[PersonID, Person] = {}

        if hasattr(self._person_repo, "set_llm_service"):
            self._person_repo.set_llm_service(self._llm_service)
        self._current_execution_id: str | None = None

    def get_or_create_person(
        self,
        person_id: PersonID,
        name: str | None = None,
        llm_config: PersonLLMConfig | None = None,
        diagram: Any | None = None,
    ) -> Person:
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
        self._person_repo.register_person(person_id, config)

    def get_person(self, person_id: PersonID) -> Person:
        return self._person_repo.get(person_id)

    def get_all_persons(self) -> dict[PersonID, Person]:
        return self._person_repo.get_all()

    def get_llm_service(self):
        return self._llm_service

    def get_conversation(self):
        if self._conversation_repo:
            return self._conversation_repo.get_global_conversation()
        return None

    def add_message(self, message: Message, execution_id: str, node_id: str | None = None) -> None:
        self._current_execution_id = execution_id

        if self._conversation_repo:
            self._conversation_repo.add_message(message, execution_id, node_id)

        if execution_id not in self._execution_logs:
            self._execution_logs[execution_id] = []

        self._execution_logs[execution_id].append(
            {
                "role": self._get_role_from_message(message),
                "content": message.content,
                "from_person_id": str(message.from_person_id),
                "to_person_id": str(message.to_person_id),
                "node_id": node_id,
                "timestamp": message.timestamp,
            }
        )

    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        person_id_obj = PersonID(person_id)

        if not self._person_repo.exists(person_id_obj):
            return []

        if self._conversation_repo:
            history = self._conversation_repo.get_conversation_history(person_id_obj)
        else:
            history = []

        if self._current_execution_id:
            for entry in history:
                entry["execution_id"] = self._current_execution_id

        return history

    def clear_all_conversations(self) -> None:
        if self._conversation_repo:
            self._conversation_repo.clear()

        for _person_id, person in self._person_repo.get_all().items():
            person.set_memory_limit(-1)
            person.set_memory_view(person.memory_view)

        self._execution_logs.clear()
        self._current_execution_id = None

    async def initialize(self) -> None:
        pass

    @staticmethod
    def _get_role_from_message(message: Message) -> str:
        if message.from_person_id == "system":
            return "system"
        elif message.from_person_id == message.to_person_id:
            return "assistant"
        else:
            return "user"

    def get_person_config(self, person_id: str) -> PersonLLMConfig | None:
        person_id_obj = PersonID(person_id)
        if self._person_repo.exists(person_id_obj):
            person = self._person_repo.get(person_id_obj)
            return person.llm_config
        return None

    async def make_llm_decision(
        self,
        person_id: PersonID,
        prompt: str,
        template_values: dict[str, Any] | None = None,
        memory_profile: str = "GOLDFISH",
        diagram: Any | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Make LLM decision using direct LLMInfraService method."""
        if not self._llm_service:
            return False, {"error": "LLM service not available"}

        # Get or create person to get LLM config
        person = self.get_or_create_person(person_id, diagram=diagram)
        llm_config = person.llm_config

        # Use LLMInfraService's complete_decision method directly
        output = await self._llm_service.complete_decision(
            prompt=prompt,
            context=template_values or {},
            model=llm_config.model,
            api_key_id=llm_config.api_key_id.value
            if hasattr(llm_config.api_key_id, "value")
            else str(llm_config.api_key_id),
            service_name=llm_config.service.value
            if hasattr(llm_config.service, "value")
            else str(llm_config.service),
        )

        # Build metadata for compatibility
        metadata = {
            "decision": output.decision,
            "memory_profile": memory_profile,
            "person": str(person_id),
        }

        return output.decision, metadata

    def load_prompt(
        self,
        prompt_file: str | None = None,
        inline_prompt: str | None = None,
        diagram: Any | None = None,
        node_label: str | None = None,
    ) -> str | None:
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

    def _create_person_from_diagram(self, person_id: PersonID, diagram: Any) -> Person | None:
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
            loaded_prompt = self.load_prompt(
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
            prompt_file=None,  # Clear prompt_file since we've already loaded it
        )

        person = self._person_repo.get_or_create(
            person_id=person_id,
            name=person_config.get("name", str(person_id)),
            llm_config=llm_config,
        )

        return person

    def register_diagram_persons(self, diagram: Any) -> None:
        # Check if diagram has persons in metadata (ExecutableDiagram)
        persons_catalog = None
        if hasattr(diagram, "metadata") and isinstance(diagram.metadata, dict):
            persons_catalog = diagram.metadata.get("persons", {})
        # Fallback to direct persons attribute (DomainDiagram)
        elif hasattr(diagram, "persons"):
            # Convert persons to catalog format (same logic as _create_person_from_diagram)
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
