"""Service for preparing diagrams for execution."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from dipeo.application.execution.use_cases.diagram_helpers import (
    extract_api_keys_from_domain,
    register_todo_diagram_if_needed,
)
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import DiagramMetadata, DomainDiagram
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin
from dipeo.domain.diagram.models import ExecutableDiagram
from dipeo.infrastructure.security.keys import APIKeyService as APIKeyDomainService

if TYPE_CHECKING:
    from dipeo.application.diagram.use_cases import (
        CompileDiagramUseCase,
        LoadDiagramUseCase,
        ValidateDiagramUseCase,
    )
    from dipeo.application.registry import ServiceRegistry

logger = get_module_logger(__name__)


class PrepareDiagramForExecutionUseCase(LoggingMixin, InitializationMixin):
    """Prepares diagrams for execution by the engine."""

    def __init__(
        self,
        api_key_service: APIKeyDomainService,
        service_registry: Optional["ServiceRegistry"] = None,
    ):
        # Initialize mixins
        InitializationMixin.__init__(self)
        self.api_key_service = api_key_service
        self.service_registry = service_registry

        # Lazy-loaded use cases
        self._load_diagram_use_case: LoadDiagramUseCase | None = None
        self._validate_diagram_use_case: ValidateDiagramUseCase | None = None
        self._compile_diagram_use_case: CompileDiagramUseCase | None = None

    async def initialize(self) -> None:
        # No longer need to initialize diagram service directly
        pass

    def _get_load_diagram_use_case(self) -> "LoadDiagramUseCase":
        """Get or resolve the LoadDiagramUseCase."""
        if self._load_diagram_use_case is None and self.service_registry:
            from dipeo.application.registry.keys import LOAD_DIAGRAM_USE_CASE

            self._load_diagram_use_case = self.service_registry.resolve(LOAD_DIAGRAM_USE_CASE)
        return self._load_diagram_use_case

    def _get_validate_diagram_use_case(self) -> "ValidateDiagramUseCase":
        """Get or resolve the ValidateDiagramUseCase."""
        if self._validate_diagram_use_case is None and self.service_registry:
            from dipeo.application.registry.keys import VALIDATE_DIAGRAM_USE_CASE

            self._validate_diagram_use_case = self.service_registry.resolve(
                VALIDATE_DIAGRAM_USE_CASE
            )
        return self._validate_diagram_use_case

    def _get_compile_diagram_use_case(self) -> "CompileDiagramUseCase":
        """Get or resolve the CompileDiagramUseCase."""
        if self._compile_diagram_use_case is None and self.service_registry:
            from dipeo.application.registry.keys import COMPILE_DIAGRAM_USE_CASE

            self._compile_diagram_use_case = self.service_registry.resolve(COMPILE_DIAGRAM_USE_CASE)
        return self._compile_diagram_use_case

    async def prepare_for_execution(
        self,
        diagram: str | DomainDiagram,
        diagram_id: str | None = None,
        validate: bool = True,
    ) -> ExecutableDiagram:
        """Prepare any diagram input for execution.

        Args:
            diagram: Can be:
                - str: diagram ID to load from storage
                - DomainDiagram: already parsed domain model
            diagram_id: Optional ID to use (for in-memory diagrams)
            validate: Whether to validate the diagram

        Returns:
            ExecutableDiagram ready for the engine
        """
        # Step 1: Get the domain diagram
        diagram_source_path = None
        if isinstance(diagram, str):
            # Store the source path for later use
            diagram_source_path = diagram
            # Use LoadDiagramUseCase to load from file
            load_use_case = self._get_load_diagram_use_case()
            domain_diagram = await load_use_case.load_diagram(diagram_name=diagram)
        elif isinstance(diagram, DomainDiagram):
            # Already have domain model
            domain_diagram = diagram
            # If diagram_id is provided for a DomainDiagram, use it as source path
            if diagram_id:
                diagram_source_path = diagram_id
        else:
            raise ValueError(f"Unsupported diagram type: {type(diagram)}")

        # Step 2: Validate if requested
        if validate:
            # Use ValidateDiagramUseCase to validate the domain diagram
            validate_use_case = self._get_validate_diagram_use_case()
            validation_result = validate_use_case.validate(domain_diagram)
            if not validation_result.is_valid:
                error_msg = "Diagram validation failed: " + "; ".join(validation_result.errors)
                raise ValueError(error_msg)
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"Diagram validation warning: {warning}")

        # Step 3: Fix API keys and extract them
        # Extract API keys directly from DomainDiagram
        api_keys = extract_api_keys_from_domain(domain_diagram, self.api_key_service)

        # Step 4: Update metadata if needed
        if diagram_id and (not domain_diagram.metadata or not domain_diagram.metadata.id):
            if not domain_diagram.metadata:
                domain_diagram.metadata = DiagramMetadata(
                    id=diagram_id,
                    name=diagram_id,
                    version="2.0.0",
                    created=datetime.now(UTC).isoformat(),
                    modified=datetime.now(UTC).isoformat(),
                )
            else:
                # Update the metadata ID
                metadata_dict = domain_diagram.metadata.model_dump()
                metadata_dict["id"] = diagram_id
                domain_diagram.metadata = DiagramMetadata(**metadata_dict)

        # Step 5: Compile diagram to ExecutableDiagram using CompileDiagramUseCase
        compile_use_case = self._get_compile_diagram_use_case()
        executable_diagram = compile_use_case.compile(domain_diagram)
        # Add API keys to metadata
        executable_diagram.metadata["api_keys"] = api_keys

        # Store persons in metadata for sub_diagram execution
        if hasattr(domain_diagram, "persons") and domain_diagram.persons:
            persons_dict = {}
            # Handle both dict and list formats
            persons_list = (
                list(domain_diagram.persons.values())
                if isinstance(domain_diagram.persons, dict)
                else domain_diagram.persons
            )
            for person in persons_list:
                person_id = str(person.id) if hasattr(person, "id") else str(person.name)
                person_config = {}

                # Extract LLM config
                if hasattr(person, "llm_config"):
                    llm_config = person.llm_config
                    # Extract the enum value (not the string representation)
                    service_value = (
                        llm_config.service if hasattr(llm_config, "service") else "openai"
                    )
                    # If it's an enum, get its value, otherwise use as-is
                    if hasattr(service_value, "value"):
                        person_config["service"] = service_value.value
                    else:
                        person_config["service"] = str(service_value)

                    person_config["model"] = (
                        str(llm_config.model)
                        if hasattr(llm_config, "model")
                        else "gpt-5-nano-2025-08-07"
                    )
                    person_config["api_key_id"] = (
                        str(llm_config.api_key_id)
                        if hasattr(llm_config, "api_key_id")
                        else "default"
                    )

                    # Add system prompt if available
                    if hasattr(llm_config, "system_prompt") and llm_config.system_prompt:
                        person_config["system_prompt"] = llm_config.system_prompt

                persons_dict[person_id] = person_config

            executable_diagram.metadata["persons"] = persons_dict
            logger.debug(f"Added {len(persons_dict)} persons to executable diagram metadata")

        # Store the diagram ID in metadata for tracking
        if diagram_id:
            executable_diagram.metadata["diagram_id"] = diagram_id

        # Store the diagram source path for prompt resolution
        if diagram_source_path:
            executable_diagram.metadata["diagram_source_path"] = diagram_source_path
            # Also store as diagram_id if not already set
            if not diagram_id:
                executable_diagram.metadata["diagram_id"] = diagram_source_path

        # Check if this is a TO-DO-backed diagram and register for monitoring
        # await register_todo_diagram_if_needed(
        #     self.todo_sync_service, domain_diagram, executable_diagram
        # )

        return executable_diagram
