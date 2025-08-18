"""Service for preparing diagrams for execution."""

import logging
from datetime import UTC, datetime
from typing import Optional, TYPE_CHECKING

from dipeo.application.integrations.use_cases import APIKeyService as APIKeyDomainService
from dipeo.domain.base import BaseService
from dipeo.domain.diagram.models import ExecutableDiagram
from dipeo.domain.diagram.validation.diagram_validator import DiagramValidator
from dipeo.diagram_generated import DiagramMetadata, DomainDiagram

if TYPE_CHECKING:
    from dipeo.application.registry import ServiceRegistry
    from dipeo.infrastructure.services.diagram import DiagramService

# Compiler imported inline where used

logger = logging.getLogger(__name__)


class PrepareDiagramForExecutionUseCase(BaseService):
    """Prepares diagrams for execution by the engine."""

    def __init__(
        self,
        diagram_service: "DiagramService",
        validator: DiagramValidator,
        api_key_service: APIKeyDomainService,
        service_registry: Optional["ServiceRegistry"] = None,
    ):
        super().__init__()
        self.diagram_service = diagram_service
        self.validator = validator
        self.api_key_service = api_key_service
        self.service_registry = service_registry

    async def initialize(self) -> None:
        # Initialize diagram service if available
        if self.diagram_service and hasattr(self.diagram_service, 'initialize'):
            await self.diagram_service.initialize()

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
            # Load from diagram service
            # Ensure diagram service is initialized
            if hasattr(self.diagram_service, 'initialize'):
                await self.diagram_service.initialize()
            domain_diagram = await self.diagram_service.load_from_file(diagram)
        elif isinstance(diagram, DomainDiagram):
            # Already have domain model
            domain_diagram = diagram
        else:
            raise ValueError(f"Unsupported diagram type: {type(diagram)}")

        # Step 2: Validate if requested
        if validate:
            # For now, skip validation for DomainDiagram since validator expects dict format
            # TODO: Update validator to work with DomainDiagram directly
            logger.debug("Skipping validation for DomainDiagram (not yet implemented)")

        # Step 3: Fix API keys and extract them
        # Extract API keys directly from DomainDiagram
        api_keys = self._extract_api_keys_from_domain(domain_diagram)

        # Step 4: Update metadata if needed
        if diagram_id and (
            not domain_diagram.metadata or not domain_diagram.metadata.id
        ):
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

        # Step 5: Compile diagram to ExecutableDiagram with static types
        # Try to get compiler from service registry if available
        compiler = None
        if self.service_registry:
            from dipeo.application.registry.registry_tokens import DIAGRAM_COMPILER
            compiler = self.service_registry.resolve(DIAGRAM_COMPILER)
        
        # Fallback to creating compiler adapter directly if not in registry
        if not compiler:
            from dipeo.infrastructure.diagram.adapters import StandardCompilerAdapter
            compiler = StandardCompilerAdapter(use_interface_based=True)
        
        executable_diagram = compiler.compile(domain_diagram)
        # Add API keys to metadata
        executable_diagram.metadata["api_keys"] = api_keys
        
        # Store the diagram ID in metadata for tracking
        if diagram_id:
            executable_diagram.metadata["diagram_id"] = diagram_id
        
        # Store the diagram source path for prompt resolution
        if diagram_source_path:
            executable_diagram.metadata["diagram_source_path"] = diagram_source_path
            # Also store as diagram_id if not already set
            if not diagram_id:
                executable_diagram.metadata["diagram_id"] = diagram_source_path
        
        return executable_diagram



    def _extract_api_keys_from_domain(self, diagram: DomainDiagram) -> dict[str, str]:
        """Extract API keys needed for execution from DomainDiagram."""
        keys = {}
        
        # Get all available API keys
        all_keys = {
            info["id"]: self.api_key_service.get_api_key(info["id"])["key"]
            for info in self.api_key_service.list_api_keys()
        }

        # Extract API keys from persons
        if hasattr(diagram, 'persons') and diagram.persons:
            # Handle both dict and list formats
            persons_list = list(diagram.persons.values()) if isinstance(diagram.persons, dict) else diagram.persons
            for person in persons_list:
                # Get api_key_id from llm_config
                if hasattr(person, 'llm_config') and hasattr(person.llm_config, 'api_key_id'):
                    api_key_id = str(person.llm_config.api_key_id)
                    
                    # Add the API key to the keys dict if it exists
                    if api_key_id in all_keys:
                        keys[api_key_id] = all_keys[api_key_id]
                    else:
                        logger.warning(f"API key {api_key_id} not found in available keys")

        return keys

