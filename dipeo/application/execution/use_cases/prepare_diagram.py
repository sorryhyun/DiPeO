"""Service for preparing diagrams for execution."""

import logging
from datetime import UTC, datetime
from typing import Any

from dipeo.application.services.apikey_service import APIKeyService as APIKeyDomainService
from dipeo.application.services.diagram_service import DiagramService as DiagramStorageDomainService
from dipeo.core import BaseService, ValidationError
from dipeo.core.static import ExecutableDiagram
from dipeo.domain.diagram.utils import (
    dict_to_domain_diagram,
    domain_diagram_to_dict,
)
from dipeo.domain.validators import DiagramValidator
from dipeo.models import DiagramMetadata, DomainDiagram

from ...resolution import StaticDiagramCompiler

logger = logging.getLogger(__name__)


class PrepareDiagramForExecutionUseCase(BaseService):
    """Prepares diagrams for execution by the engine."""

    def __init__(
        self,
        storage_service: DiagramStorageDomainService,
        validator: DiagramValidator,
        api_key_service: APIKeyDomainService,
    ):
        super().__init__()
        self.storage = storage_service
        self.validator = validator
        self.api_key_service = api_key_service

    async def initialize(self) -> None:
        await self.storage.initialize()

    async def prepare_for_execution(
        self,
        diagram: str | dict[str, Any] | DomainDiagram,
        diagram_id: str | None = None,
        validate: bool = True,
    ) -> ExecutableDiagram:
        """Prepare any diagram input for execution.

        Args:
            diagram: Can be:
                - str: diagram ID to load from storage
                - Dict: raw diagram data (backend or domain format)
                - DomainDiagram: already parsed domain model
            diagram_id: Optional ID to use (for in-memory diagrams)
            validate: Whether to validate the diagram

        Returns:
            ExecutableDiagram ready for the engine
        """
        # Step 1: Get the domain diagram
        if isinstance(diagram, str):
            # Load from storage
            diagram_id = diagram
            backend_data = await self._load_from_storage(diagram_id)
            # Convert to domain model
            if self._is_backend_format(backend_data):
                domain_diagram = dict_to_domain_diagram(backend_data)
            else:
                domain_diagram = DomainDiagram.model_validate(backend_data)
        elif isinstance(diagram, DomainDiagram):
            # Already have domain model
            domain_diagram = diagram
        elif isinstance(diagram, dict):
            # Raw dict - could be backend or domain format
            if self._is_backend_format(diagram):
                domain_diagram = dict_to_domain_diagram(diagram)
            else:
                # Domain format dict
                domain_diagram = DomainDiagram.model_validate(diagram)
        else:
            raise ValueError(f"Unsupported diagram type: {type(diagram)}")

        # Step 2: Validate if requested
        if validate:
            # Convert to dict format for validation
            backend_data = domain_diagram_to_dict(domain_diagram)
            
            # Validate using domain validator
            result = self.validator.validate(backend_data)
            if not result.is_valid:
                error_messages = [str(error) for error in result.errors]
                raise ValidationError(f"Diagram validation failed: {'; '.join(error_messages)}")

        # Step 3: Fix API keys and extract them
        # Work with dict format for API key handling
        backend_data = domain_diagram_to_dict(domain_diagram)
        backend_data = self._fix_api_key_references(backend_data)
        api_keys = self._extract_api_keys(backend_data)
        
        # Convert back to domain model with fixed API keys
        domain_diagram = dict_to_domain_diagram(backend_data)

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
        logger.info("Compiling diagram with StaticDiagramCompiler")
        import time
        start_time = time.time()
        compiler = StaticDiagramCompiler()
        executable_diagram = compiler.compile(domain_diagram)
        # Add API keys to metadata
        executable_diagram.metadata["api_keys"] = api_keys
        compile_time = time.time() - start_time
        logger.info(f"Diagram compilation took {compile_time:.3f}s")
        
        # Store the diagram ID in metadata for tracking
        if diagram_id:
            executable_diagram.metadata["diagram_id"] = diagram_id
        
        return executable_diagram

    async def _load_from_storage(self, diagram_id: str) -> dict[str, Any]:
        """Load diagram from storage."""
        logger.info(f"Loading diagram {diagram_id} from storage")

        if diagram_id == "quicksave":
            path = "quicksave.json"
        else:
            found_path = await self.storage.find_by_id(diagram_id)
            if not found_path:
                raise FileNotFoundError(f"Diagram not found: {diagram_id}")
            path = found_path

        logger.debug(f"Loading diagram from {path}")
        return await self.storage.read_file(path)

    def _is_backend_format(self, data: dict[str, Any]) -> bool:
        """Check if data is in backend format (dict-based nodes)."""
        if "nodes" in data and isinstance(data["nodes"], dict):
            first_node = (
                next(iter(data["nodes"].values()), None) if data["nodes"] else None
            )
            if first_node and isinstance(first_node, dict):
                return True
        return False

    def _fix_api_key_references(self, diagram: dict[str, Any]) -> dict[str, Any]:
        """Fix invalid API key references in diagram."""
        valid_api_keys = {key["id"] for key in self.api_key_service.list_api_keys()}

        persons = diagram.get("persons", {})
        if not isinstance(persons, dict):
            raise ValidationError(
                "Persons must be a dictionary with person IDs as keys"
            )

        for person in persons.values():
            api_key_id = person.get("apiKeyId") or person.get("api_key_id")
            if api_key_id and api_key_id not in valid_api_keys:
                all_keys = self.api_key_service.list_api_keys()
                fallback = next(
                    (k for k in all_keys if k["service"] == person.get("service")), None
                )
                if fallback:
                    logger.info(
                        f"Replaced invalid API key {api_key_id} with {fallback['id']}"
                    )
                    if "api_key_id" in person:
                        person["api_key_id"] = fallback["id"]
                    else:
                        person["api_key_id"] = fallback["id"]
                else:
                    raise ValidationError(
                        f"No valid API key found for service: {person.get('service')}"
                    )

        return diagram

    def _extract_api_keys(self, diagram: dict[str, Any]) -> dict[str, str]:
        """Extract API keys needed for execution."""
        keys = {}

        all_keys = {
            info["id"]: self.api_key_service.get_api_key(info["id"])["key"]
            for info in self.api_key_service.list_api_keys()
        }

        persons = diagram.get("persons", {})
        for person in persons.values():
            api_key_id = person.get("apiKeyId") or person.get("api_key_id")
            if api_key_id and api_key_id in all_keys:
                keys[api_key_id] = all_keys[api_key_id]

        return keys

