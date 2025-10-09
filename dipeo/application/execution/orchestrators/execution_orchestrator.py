"""Execution orchestrator that coordinates repositories during diagram execution."""

import logging
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.orchestrators.person_cache import PersonCache
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import Message, PersonID, PersonLLMConfig
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
        memory_selector: Any = None,
        llm_service: Optional["LLMServicePort"] = None,
    ):
        self._person_repo = person_repository
        self._conversation_repo = conversation_repository
        self._prompt_loading_use_case = prompt_loading_use_case
        self._memory_selector = memory_selector
        self._llm_service = llm_service
        self._execution_logs: dict[str, list[dict[str, Any]]] = {}

        self._person_cache = PersonCache(person_repository, prompt_loading_use_case)

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
        """Get or create a person (delegates to PersonCache)."""
        return self._person_cache.get_or_create_person(person_id, name, llm_config, diagram)

    def register_person(self, person_id: str, config: dict[str, Any]) -> None:
        """Register a person with configuration."""
        self._person_cache.register_person(person_id, config)

    def get_person(self, person_id: PersonID) -> Person:
        """Get a person from the repository."""
        return self._person_cache.get_person(person_id)

    def get_all_persons(self) -> dict[PersonID, Person]:
        """Get all persons from the repository."""
        return self._person_cache.get_all_persons()

    def get_person_config(self, person_id: str) -> PersonLLMConfig | None:
        """Get LLM configuration for a person."""
        return self._person_cache.get_person_config(person_id)

    def register_diagram_persons(self, diagram: Any) -> None:
        """Register all persons from a diagram."""
        self._person_cache.register_diagram_persons(diagram)

    def get_llm_service(self):
        """Get the LLM service instance."""
        return self._llm_service

    def get_conversation(self):
        """Get the global conversation."""
        if self._conversation_repo:
            return self._conversation_repo.get_global_conversation()
        return None

    def add_message(self, message: Message, execution_id: str, node_id: str | None = None) -> None:
        """Add a message to the conversation and execution logs."""
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
        """Get conversation history for a person."""
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
        """Clear all conversations and execution logs."""
        if self._conversation_repo:
            self._conversation_repo.clear()

        for _person_id, person in self._person_repo.get_all().items():
            person.set_memory_limit(-1)
            person.set_memory_view(person.memory_view)

        self._execution_logs.clear()
        self._current_execution_id = None

    async def initialize(self) -> None:
        """Initialize the orchestrator."""
        pass

    @staticmethod
    def _get_role_from_message(message: Message) -> str:
        """Determine the role from a message."""
        if message.from_person_id == "system":
            return "system"
        elif message.from_person_id == message.to_person_id:
            return "assistant"
        else:
            return "user"

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

        person = self.get_or_create_person(person_id, diagram=diagram)
        llm_config = person.llm_config

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
        """Load a prompt from file or inline."""
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
