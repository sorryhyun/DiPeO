"""Service for preparing diagrams for execution."""

import logging
from datetime import UTC, datetime
from typing import Optional, TYPE_CHECKING

from dipeo.application.services.apikey_service import APIKeyService as APIKeyDomainService
from dipeo.core import BaseService, ValidationError
from dipeo.core.ports.diagram_port import DiagramPort as DiagramStorageDomainService
from dipeo.domain.diagram.models import ExecutableDiagram
from dipeo.domain.validators import DiagramValidator
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
        storage_service: DiagramStorageDomainService,
        validator: DiagramValidator,
        api_key_service: APIKeyDomainService,
        service_registry: Optional["ServiceRegistry"] = None,
        diagram_service: Optional["DiagramService"] = None,
    ):
        super().__init__()
        self.storage = storage_service
        self.validator = validator
        self.api_key_service = api_key_service
        self.service_registry = service_registry
        self.diagram_service = diagram_service

    async def initialize(self) -> None:
        # Initialize storage if it has an initialize method
        if hasattr(self.storage, 'initialize'):
            await self.storage.initialize()
        
        # Initialize diagram service if not provided and available in registry
        if not self.diagram_service and self.service_registry:
            from dipeo.application.registry import DIAGRAM_SERVICE_NEW
            try:
                self.diagram_service = self.service_registry.resolve(DIAGRAM_SERVICE_NEW)
            except:
                pass
        
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
        if isinstance(diagram, str):
            # Load from storage using diagram service if available
            if self.diagram_service:
                # Ensure diagram service is initialized
                if hasattr(self.diagram_service, 'initialize'):
                    await self.diagram_service.initialize()
                try:
                    domain_diagram = await self.diagram_service.load_from_file(diagram)
                except FileNotFoundError:
                    # Fallback to storage service for diagram ID
                    domain_diagram = await self._load_from_storage(diagram)
            else:
                # Load directly from storage as DomainDiagram
                domain_diagram = await self._load_from_storage(diagram)
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
        logger.info("Compiling diagram with CompilationService")
        import time
        start_time = time.time()
        
        # Try to get compiler from service registry if available
        compiler = None
        if self.service_registry:
            from dipeo.application.registry import COMPILATION_SERVICE
            compiler = self.service_registry.resolve(COMPILATION_SERVICE)
        
        # Fallback to creating compiler directly if not in registry
        if not compiler:
            from dipeo.infrastructure.services.diagram.compilation_service import CompilationService
            compiler = CompilationService()
            await compiler.initialize()
        
        executable_diagram = compiler.compile(domain_diagram)
        # Add API keys to metadata
        executable_diagram.metadata["api_keys"] = api_keys
        compile_time = time.time() - start_time
        logger.info(f"Diagram compilation took {compile_time:.3f}s")
        
        # Store the diagram ID in metadata for tracking
        if diagram_id:
            executable_diagram.metadata["diagram_id"] = diagram_id
        
        return executable_diagram

    async def _load_from_storage(self, diagram_id: str) -> DomainDiagram:
        """Load diagram from storage and return as DomainDiagram."""
        logger.info(f"Loading diagram {diagram_id} from storage")

        # If we have a DiagramStorageAdapter with load_diagram_model, use it
        if hasattr(self.storage, 'load_diagram_model'):
            try:
                # This returns a DomainDiagram directly
                return await self.storage.load_diagram_model(diagram_id)
            except Exception as e:
                logger.error(f"Failed to load diagram model: {e}")
                raise FileNotFoundError(f"Diagram not found: {diagram_id}")
        
        # Fallback: If storage doesn't support typed loading, load raw and convert
        # This shouldn't happen with proper DiagramStorageAdapter, but kept for safety
        if hasattr(self.storage, 'load_diagram'):
            content, format = await self.storage.load_diagram(diagram_id)
            # Use converter service to deserialize
            from dipeo.infrastructure.services.diagram import DiagramConverterService
            converter = DiagramConverterService()
            await converter.initialize()
            return converter.deserialize_from_storage(content, format)
        
        raise NotImplementedError("Storage adapter doesn't support diagram loading")


    def _extract_api_keys_from_domain(self, diagram: DomainDiagram) -> dict[str, str]:
        """Extract API keys needed for execution from DomainDiagram."""
        keys = {}
        valid_api_keys = {key["id"] for key in self.api_key_service.list_api_keys()}
        all_keys = {
            info["id"]: self.api_key_service.get_api_key(info["id"])["key"]
            for info in self.api_key_service.list_api_keys()
        }

        # Handle persons in DomainDiagram format
        if hasattr(diagram, 'persons') and diagram.persons:
            # Handle both dict and list formats
            persons_list = list(diagram.persons.values()) if isinstance(diagram.persons, dict) else diagram.persons
            for person in persons_list:
                api_key_id = None
                # Check for api_key_id in various places
                if hasattr(person, 'api_key_id'):
                    api_key_id = person.api_key_id
                elif hasattr(person, 'apiKeyId'):
                    api_key_id = person.apiKeyId
                elif hasattr(person, 'llm_config'):
                    # Handle nested llm_config structure
                    if hasattr(person.llm_config, 'api_key_id'):
                        api_key_id = person.llm_config.api_key_id
                    elif hasattr(person.llm_config, 'apiKeyId'):
                        api_key_id = person.llm_config.apiKeyId
                
                # Validate and fix API key if needed
                if api_key_id:
                    if api_key_id not in valid_api_keys:
                        # Try to find a fallback API key
                        service = None
                        if hasattr(person, 'service'):
                            service = person.service
                        elif hasattr(person, 'llm_config') and hasattr(person.llm_config, 'service'):
                            service = person.llm_config.service
                            # Handle enum values
                            if hasattr(service, 'value'):
                                service = service.value
                        
                        if service:
                            all_service_keys = self.api_key_service.list_api_keys()
                            fallback = next(
                                (k for k in all_service_keys if k["service"] == service), None
                            )
                            if fallback:
                                logger.info(
                                    f"Replaced invalid API key {api_key_id} with {fallback['id']}"
                                )
                                api_key_id = fallback['id']
                                # Update the person's API key reference
                                if hasattr(person, 'api_key_id'):
                                    person.api_key_id = api_key_id
                                elif hasattr(person, 'apiKeyId'):
                                    person.apiKeyId = api_key_id
                                elif hasattr(person, 'llm_config'):
                                    if hasattr(person.llm_config, 'api_key_id'):
                                        person.llm_config.api_key_id = api_key_id
                                    elif hasattr(person.llm_config, 'apiKeyId'):
                                        person.llm_config.apiKeyId = api_key_id
                            else:
                                raise ValidationError(
                                    f"No valid API key found for service: {service}"
                                )
                    
                    # Add the API key to the keys dict
                    if api_key_id in all_keys:
                        keys[api_key_id] = all_keys[api_key_id]

        return keys

