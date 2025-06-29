"""GraphQL mutations for file upload support (GraphQL multipart spec)."""

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import strawberry
from dipeo_diagram import (
    BackendDiagram,
    backend_to_graphql,
    converter_registry,
)
from dipeo_domain import (
    DiagramMetadata,
    DomainDiagram,
)
from strawberry.file_uploads import Upload

from config import BASE_DIR
from dipeo_server.domains.apikey import APIKeyDomainService

from ..context import GraphQLContext
from ..types import (
    DiagramFormat,
    FileUploadResult,
    JSONScalar,
)

logger = logging.getLogger(__name__)


def validate_diagram(
    diagram: DomainDiagram, api_key_service: APIKeyDomainService | None = None
) -> list[str]:
    """Validates diagram structure, returns error list."""
    errors = []

    if not diagram.nodes:
        errors.append("Diagram must have at least one node")

    node_ids = {node.id for node in diagram.nodes}
    handle_ids = {handle.id for handle in diagram.handles}

    for arrow in diagram.arrows:
        if arrow.source not in handle_ids:
            source_node_id = arrow.source.split(":")[0]
            if source_node_id not in node_ids:
                errors.append(
                    f"Arrow {arrow.id} references unknown source: {arrow.source}"
                )

        if arrow.target not in handle_ids:
            target_node_id = arrow.target.split(":")[0]
            if target_node_id not in node_ids:
                errors.append(
                    f"Arrow {arrow.id} references unknown target: {arrow.target}"
                )

    for handle in diagram.handles:
        if handle.node_id not in node_ids:
            errors.append(
                f"Handle {handle.id} references unknown node: {handle.node_id}"
            )

    person_ids = {person.id for person in diagram.persons}
    for node in diagram.nodes:
        person_id = node.data.get("personId") if node.data else None
        if person_id and person_id not in person_ids:
            errors.append(f"Node {node.id} references unknown person: {person_id}")

    if api_key_service:
        api_key_ids = {
            api_key.get("id", "") for api_key in api_key_service.list_api_keys()
        }
        for person in diagram.persons:
            if person.api_key_id and person.api_key_id not in api_key_ids:
                errors.append(
                    f"Person {person.id} references unknown API key: {person.api_key_id}"
                )
    else:
        api_key_ids = {api_key.id for api_key in diagram.api_keys}
        for person in diagram.persons:
            if person.api_key_id and person.api_key_id not in api_key_ids:
                errors.append(
                    f"Person {person.id} references unknown API key: {person.api_key_id}"
                )

    return errors


def domain_to_backend_format(diagram: DomainDiagram) -> dict[str, Any]:
    """Converts domain diagram to backend dict format."""
    converter = converter_registry.get(DiagramFormat.native.value)
    json_str = converter.serialize(diagram)
    data = json.loads(json_str)

    if isinstance(data.get("nodes"), list):
        data["nodes"] = {node["id"]: node for node in data["nodes"]}
    if isinstance(data.get("arrows"), list):
        data["arrows"] = {arrow["id"]: arrow for arrow in data["arrows"]}
    if isinstance(data.get("handles"), list):
        data["handles"] = {handle["id"]: handle for handle in data["handles"]}
    if isinstance(data.get("persons"), list):
        data["persons"] = {person["id"]: person for person in data["persons"]}
    if isinstance(data.get("api_keys"), list):
        data["api_keys"] = {api_key["id"]: api_key for api_key in data["api_keys"]}

    return data


def backend_to_domain_format(data: dict[str, Any]) -> DomainDiagram:
    """Converts backend dict to domain diagram."""
    converter = converter_registry.get(DiagramFormat.native.value)
    json_str = json.dumps(data, indent=2)
    return converter.deserialize(json_str)


@strawberry.type
class DiagramValidationResult:
    """Result of diagram validation."""

    is_valid: bool
    errors: list[str] = strawberry.field(default_factory=list)
    node_count: int | None = None
    arrow_count: int | None = None
    person_count: int | None = None


@strawberry.type
class DiagramConvertResult:
    """Result of diagram format conversion."""

    success: bool
    message: str = ""
    error: str | None = None
    content: str | None = None
    format: str | None = None
    filename: str | None = None


@strawberry.type
class UploadMutations:
    """Handles file uploads and diagram operations."""

    @strawberry.mutation(description="Upload a file to the server")
    async def upload_file(
        self, file: Upload, category: str = "general"
    ) -> FileUploadResult:
        try:
            filename = file.filename
            file_content = await file.read()
            file_size = len(file_content)

            if file_size > 10 * 1024 * 1024:
                return FileUploadResult(
                    success=False, message="File size exceeds 10MB limit"
                )

            # Special handling for diagram files
            if category.startswith("diagrams/"):
                # Save directly to files/diagrams/{format}/ instead of files/uploads/
                upload_base = BASE_DIR / "files"
                category_dir = upload_base / category
                category_dir.mkdir(parents=True, exist_ok=True)
                # Use original filename for diagrams (no UUID prefix)
                file_path = category_dir / filename
            else:
                # Regular upload flow for other files
                upload_base = BASE_DIR / "files" / "uploads"
                category_dir = upload_base / category
                category_dir.mkdir(parents=True, exist_ok=True)
                file_id = f"{uuid.uuid4().hex[:8]}_{filename}"
                file_path = category_dir / file_id

            with file_path.open("wb") as f:
                f.write(file_content)

            file_ext = Path(filename).suffix.lower()
            file_type = "unknown"
            if file_ext in [".json", ".yaml", ".yml"]:
                file_type = "diagram"
            elif file_ext in [".png", ".jpg", ".jpeg", ".gif", ".svg"]:
                file_type = "image"
            elif file_ext in [".csv", ".txt", ".log"]:
                file_type = "data"

            logger.info(
                f"File uploaded: {filename} -> {file_path} (size: {file_size} bytes)"
            )

            return FileUploadResult(
                success=True,
                message=f"File '{filename}' uploaded successfully",
                path=str(file_path),
                size_bytes=file_size,
                content_type=file_type,
            )

        except Exception as e:
            logger.error(f"File upload error: {e!s}")
            return FileUploadResult(
                success=False, message=f"Upload failed: {e!s}", error=str(e)
            )

    @strawberry.mutation(description="Validate a diagram structure")
    async def validate_diagram(
        self,
        info: strawberry.Info,
        diagram_content: JSONScalar,
    ) -> DiagramValidationResult:
        """Validate a diagram without saving it."""
        context: GraphQLContext = info.context

        try:
            if not isinstance(diagram_content, dict):
                return DiagramValidationResult(
                    is_valid=False, errors=["Diagram content must be a JSON object"]
                )

            # Create domain diagram from content
            try:
                backend_diagram = BackendDiagram(**diagram_content)
                domain_diagram = backend_to_graphql(backend_diagram)
            except Exception as e:
                return DiagramValidationResult(
                    is_valid=False, errors=[f"Invalid diagram structure: {e!s}"]
                )

            # Validate diagram
            validation_errors = validate_diagram(
                domain_diagram,
                context.api_key_service
                if isinstance(context.api_key_service, APIKeyService)
                else None,
            )

            if validation_errors:
                return DiagramValidationResult(is_valid=False, errors=validation_errors)

            return DiagramValidationResult(
                is_valid=True,
                errors=[],
                node_count=len(domain_diagram.nodes),
                arrow_count=len(domain_diagram.arrows),
                person_count=len(domain_diagram.persons),
            )

        except Exception as e:
            logger.error(f"Diagram validation error: {e!s}")
            return DiagramValidationResult(
                is_valid=False, errors=[f"Validation failed: {e!s}"]
            )

    @strawberry.mutation(description="Convert a diagram to a different format")
    async def convert_diagram(
        self,
        content: JSONScalar,
        target_format: DiagramFormat = DiagramFormat.native,
        include_metadata: bool = True,
    ) -> DiagramConvertResult:
        try:
            if not isinstance(content, dict):
                return DiagramConvertResult(
                    success=False,
                    error="Content must be a JSON object representing a diagram",
                )

            converter = converter_registry.get(target_format.value)
            if not converter:
                return DiagramConvertResult(
                    success=False, error=f"Unknown format: {target_format.value}"
                )

            format_info = converter_registry.get_info(target_format.value)
            if not format_info.get("supports_export", True):
                return DiagramConvertResult(
                    success=False,
                    error=f"Format '{target_format.value}' does not support export",
                )

            try:
                # Convert arrays to dictionaries for backend format
                converted_content = content.copy()

                # Convert arrays to dictionaries with ID as key
                for field in ["nodes", "arrows", "persons", "handles", "apiKeys"]:
                    if field in converted_content and isinstance(
                        converted_content[field], list
                    ):
                        converted_content[field] = {
                            item["id"]: item for item in converted_content[field]
                        }

                backend_diagram = BackendDiagram(**converted_content)
                domain_diagram = backend_to_graphql(backend_diagram)
            except Exception as e:
                return DiagramConvertResult(
                    success=False, error=f"Invalid diagram structure: {e!s}"
                )

            if not include_metadata:
                now = datetime.now(UTC).isoformat()
                domain_diagram.metadata = DiagramMetadata(
                    version="2.0.0", created=now, modified=now
                )

            content_str = converter.serialize(domain_diagram)

            diagram_name = content.get("metadata", {}).get("name", "diagram")
            extension = format_info.get("extension", ".yaml")
            filename = f"{diagram_name}{extension}"

            return DiagramConvertResult(
                success=True,
                message=f"Exported as {target_format.value} format",
                content=content_str,
                format=target_format.value,
                filename=filename,
            )

        except Exception as e:
            logger.error(f"Stateful export error: {e!s}", exc_info=True)
            return DiagramConvertResult(success=False, error=str(e))
