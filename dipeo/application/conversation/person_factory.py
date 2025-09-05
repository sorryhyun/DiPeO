"""Factory for creating Person entities with proper component wiring.

This factory separates the concern of object construction and dependency wiring
from the persistence responsibility of repositories.
"""

from typing import TYPE_CHECKING, Optional

from dipeo.diagram_generated import ApiKeyID, LLMService, PersonID, PersonLLMConfig
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.brain import CognitiveBrain

if TYPE_CHECKING:
    from dipeo.application.execution.orchestrators.execution_orchestrator import (
        ExecutionOrchestrator,
    )


class PersonFactory:
    """Factory for creating Person entities with cognitive components.

    This factory handles the complex construction of Person objects,
    including wiring up their cognitive brain components with appropriate
    memory selection implementations.
    """

    def __init__(self, orchestrator: Optional["ExecutionOrchestrator"] = None):
        """Initialize the factory with optional orchestrator.

        Args:
            orchestrator: Orchestrator for wiring brain components.
                         Can be set later via set_orchestrator.
        """
        self._orchestrator = orchestrator

    def set_orchestrator(self, orchestrator: "ExecutionOrchestrator") -> None:
        """Set the orchestrator for wiring brain components.

        This is useful when the orchestrator isn't available at factory
        construction time (e.g., to avoid circular dependencies).

        Args:
            orchestrator: The execution orchestrator
        """
        self._orchestrator = orchestrator

    def create_person(
        self, person_id: PersonID, name: str, llm_config: PersonLLMConfig, with_brain: bool = True
    ) -> Person:
        """Create a new person with optional cognitive components.

        Args:
            person_id: Unique identifier for the person
            name: Human-readable name
            llm_config: LLM configuration for the person
            with_brain: Whether to wire up cognitive brain components

        Returns:
            A fully constructed Person instance
        """
        # Create base person
        person = Person(id=person_id, name=name, llm_config=llm_config)

        # Wire up brain component if requested and orchestrator is available
        if with_brain and self._orchestrator:
            person.brain = self._create_brain()

        return person

    def create_person_with_defaults(
        self,
        person_id: PersonID,
        name: str | None = None,
        llm_config: PersonLLMConfig | None = None,
        with_brain: bool = True,
    ) -> Person:
        """Create a person with sensible defaults.

        Args:
            person_id: Unique identifier for the person
            name: Optional name (defaults to person_id string)
            llm_config: Optional LLM config (defaults to gpt-5-nano)
            with_brain: Whether to wire up cognitive brain components

        Returns:
            A fully constructed Person instance with defaults
        """
        # Apply defaults
        if not name:
            name = str(person_id)

        if not llm_config:
            # Default to APIKEY_52609F which is the most common API key in diagrams
            llm_config = PersonLLMConfig(
                service=LLMService("openai"),
                model="gpt-5-nano-2025-08-07",
                api_key_id=ApiKeyID("APIKEY_52609F"),
            )

        return self.create_person(
            person_id=person_id, name=name, llm_config=llm_config, with_brain=with_brain
        )

    def _create_brain(self) -> CognitiveBrain:
        """Create a cognitive brain component with wired dependencies.

        Returns:
            A configured CognitiveBrain instance
        """
        from dipeo.infrastructure.llm.adapters import LLMMemorySelectionAdapter

        # Create memory selector implementation using orchestrator
        memory_selector = LLMMemorySelectionAdapter(self._orchestrator)

        # Return brain with wired memory selector
        return CognitiveBrain(memory_selector=memory_selector)

    def enhance_person_with_brain(self, person: Person) -> Person:
        """Add cognitive brain components to an existing person.

        This is useful for enhancing persons that were created without
        brain components or loaded from storage.

        Args:
            person: The person to enhance

        Returns:
            The same person instance with brain components added
        """
        if not person.brain and self._orchestrator:
            person.brain = self._create_brain()

        return person
