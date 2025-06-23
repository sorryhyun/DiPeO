"""Adapter that provides a clean interface for the execution engine."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dipeo_core import BaseService, ValidationError
from dipeo_domain import DiagramID, DiagramMetadata, DomainDiagram

from dipeo_server.core.services import APIKeyService
from dipeo_server.domains.execution.validators import DiagramValidator

from .converter_service import DiagramConverterService
from .storage_service import DiagramStorageService

logger = logging.getLogger(__name__)


class ExecutionReadyDiagram:

    def __init__(
        self,
        diagram_id: str,
        storage_format: Dict[str, Any],
        api_keys: Dict[str, str],
        execution_hints: Dict[str, Any],
        domain_model: Optional[DomainDiagram] = None,
    ):
        self.diagram_id = diagram_id
        self.storage_format = storage_format
        self.api_keys = api_keys
        self.execution_hints = execution_hints
        self.domain_model = domain_model


class DiagramExecutionAdapter(BaseService):
    """Orchestrates diagram services to prepare diagrams for execution."""

    def __init__(
        self,
        storage_service: DiagramStorageService,
        converter_service: DiagramConverterService,
        validator: DiagramValidator,
        api_key_service: APIKeyService,
    ):
        super().__init__()
        self.storage = storage_service
        self.converter = converter_service
        self.validator = validator
        self.api_key_service = api_key_service

    async def initialize(self) -> None:
        await self.storage.initialize()
        await self.converter.initialize()

    async def prepare_diagram_for_execution(
        self,
        diagram_id: DiagramID,
        validate: bool = True,
    ) -> ExecutionReadyDiagram:
        """Prepare a diagram for execution by loading, validating and converting it."""
        logger.info(f"Preparing diagram {diagram_id} for execution")

        if diagram_id == "quicksave":
            path = "quicksave.json"
        else:
            found_path = await self.storage.find_by_id(diagram_id)
            if not found_path:
                raise FileNotFoundError(f"Diagram not found: {diagram_id}")
            path = found_path

        logger.debug(f"Loading diagram from {path}")
        storage_dict = await self.storage.read_file(path)

        if validate:
            logger.debug("Validating diagram for execution")
            errors = self.validator._validate_storage_format(storage_dict, context="execution")
            if errors:
                raise ValidationError(f"Diagram validation failed: {'; '.join(errors)}")

        storage_dict = self._fix_api_key_references(storage_dict)
        api_keys = self._extract_api_keys(storage_dict)
        domain_diagram = self.converter.storage_to_domain(storage_dict)
        execution_dict = self.converter.prepare_for_execution(domain_diagram, api_keys)
        return ExecutionReadyDiagram(
            diagram_id=diagram_id,
            storage_format=execution_dict,
            api_keys=api_keys,
            execution_hints=execution_dict.get("_execution_hints", {}),
            domain_model=domain_diagram,
        )

    async def prepare_diagram_dict_for_execution(
        self,
        diagram_dict: Dict[str, Any],
        diagram_id: Optional[str] = None,
        validate: bool = True,
    ) -> ExecutionReadyDiagram:
        """Prepare a diagram dictionary already in memory for execution."""
        logger.info(f"Preparing diagram dict for execution (id: {diagram_id or 'unknown'})")
        logger.info(f"[CONVERSION DEBUG] Input format check - is_storage_format: {self._is_storage_format(diagram_dict)}")

        if not self._is_storage_format(diagram_dict):
            logger.info("[CONVERSION DEBUG] Converting from domain format to storage format")
            domain_diagram = DomainDiagram.model_validate(diagram_dict)
            storage_dict = self.converter.domain_to_storage(domain_diagram)
            logger.info("[CONVERSION DEBUG] First conversion complete: domain -> storage")
        else:
            logger.info("[CONVERSION DEBUG] Already in storage format, skipping first conversion")
            storage_dict = diagram_dict

        if validate:
            errors = self.validator._validate_storage_format(storage_dict, context="execution")
            if errors:
                raise ValidationError(f"Diagram validation failed: {'; '.join(errors)}")

        storage_dict = self._fix_api_key_references(storage_dict)
        api_keys = self._extract_api_keys(storage_dict)

        logger.info("[CONVERSION DEBUG] Converting storage format back to domain model")
        domain_diagram = self.converter.storage_to_domain(storage_dict)
        logger.info("[CONVERSION DEBUG] Second conversion complete: storage -> domain")

        if diagram_id:
            if not domain_diagram.metadata:
                domain_diagram.metadata = DiagramMetadata(
                    id=diagram_id,
                    name=diagram_id,
                    version="2.0.0",
                    created=datetime.now(timezone.utc).isoformat(),
                    modified=datetime.now(timezone.utc).isoformat()
                )
            else:
                # Update the metadata ID
                metadata_dict = domain_diagram.metadata.model_dump()
                metadata_dict["id"] = diagram_id
                domain_diagram.metadata = DiagramMetadata(**metadata_dict)

        logger.info("[CONVERSION DEBUG] Preparing for execution with hints")
        execution_dict = self.converter.prepare_for_execution(domain_diagram, api_keys)
        logger.info("[CONVERSION DEBUG] Final conversion complete: domain -> execution format")

        diagram_id_final = diagram_id or (domain_diagram.metadata.id if domain_diagram.metadata else None) or "unknown"
        return ExecutionReadyDiagram(
            diagram_id=diagram_id_final,
            storage_format=execution_dict,
            api_keys=api_keys,
            execution_hints=execution_dict.get("_execution_hints", {}),
            domain_model=domain_diagram,
        )

    def _fix_api_key_references(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        valid_api_keys = {key["id"] for key in self.api_key_service.list_api_keys()}

        persons = diagram.get("persons", {})
        if not isinstance(persons, dict):
            raise ValidationError("Persons must be a dictionary with person IDs as keys")

        for person in persons.values():
            api_key_id = person.get("apiKeyId") or person.get("api_key_id")
            if api_key_id and api_key_id not in valid_api_keys:
                all_keys = self.api_key_service.list_api_keys()
                fallback = next(
                    (k for k in all_keys if k["service"] == person.get("service")),
                    None
                )
                if fallback:
                    logger.info(
                        f"Replaced invalid API key {api_key_id} with {fallback['id']}"
                    )
                    if "apiKeyId" in person:
                        person["apiKeyId"] = fallback["id"]
                    else:
                        person["api_key_id"] = fallback["id"]
                else:
                    raise ValidationError(
                        f"No valid API key found for service: {person.get('service')}"
                    )

        return diagram

    def _extract_api_keys(self, diagram: Dict[str, Any]) -> Dict[str, str]:
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

    def _is_storage_format(self, data: Dict[str, Any]) -> bool:
        if "nodes" in data and isinstance(data["nodes"], dict):
            first_node = next(iter(data["nodes"].values()), None) if data["nodes"] else None
            if first_node and isinstance(first_node, dict):
                return True
        return False

