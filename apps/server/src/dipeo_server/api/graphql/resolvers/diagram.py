"""GraphQL resolvers for diagram operations."""

import json
import logging
from collections import defaultdict
from datetime import UTC, datetime

from dipeo.infra.diagram import converter_registry
from dipeo.models import DiagramMetadata, DomainDiagram

from dipeo_server.shared.constants import DIAGRAM_VERSION

from ..types_new import (
    DiagramFilterInput,
    DiagramID,
    DomainDiagramType,
)

logger = logging.getLogger(__name__)


class DiagramResolver:
    """Handles diagram queries and data retrieval."""

    async def get_diagram(
        self, diagram_id: DiagramID, info
    ) -> DomainDiagramType | None:
        """Returns diagram by ID."""
        try:
            logger.info(f"Attempting to get diagram with ID: {diagram_id}")

            # Use integrated diagram service
            integrated_service = info.context.get_service("integrated_diagram_service")

            # Get path for format detection
            file_repo = integrated_service.file_repository
            path = await file_repo.find_by_id(diagram_id) or ""

            # Determine format from path
            format_type = "native"  # default
            if (
                "light/" in path
                or path.endswith(".light.yaml")
                or path.endswith(".light.yml")
            ):
                format_type = "light"
            elif (
                "readable/" in path
                or path.endswith(".readable.yaml")
                or path.endswith(".readable.yml")
            ):
                format_type = "readable"

            # For readable and light formats, get raw content to preserve structure
            if format_type in ("readable", "light"):
                logger.info(f"Detected {format_type} format for diagram {diagram_id}")
                raw_content = await file_repo.read_raw_content(path)
                domain_diagram = converter_registry.deserialize(
                    raw_content, format_type
                )
            else:
                # For native format, get parsed data
                diagram_data = await integrated_service.get_diagram(diagram_id)
                if not diagram_data:
                    logger.error(f"Diagram not found: {diagram_id}")
                    return None
                json_content = json.dumps(diagram_data)
                domain_diagram = converter_registry.deserialize(json_content, "native")

            # Ensure metadata is complete
            if not domain_diagram.metadata or not domain_diagram.metadata.id:
                domain_diagram.metadata = DiagramMetadata(
                    id=diagram_id,
                    name=diagram_id,
                    description=f"{format_type} format diagram",
                    version=DIAGRAM_VERSION,
                    created=datetime.now(UTC).isoformat(),
                    modified=datetime.now(UTC).isoformat(),
                )

            # Use domain model directly for GraphQL
            graphql_diagram = domain_diagram

            # Build handle index for resolver context
            handle_index = defaultdict(list)
            for handle in graphql_diagram.handles:
                handle_index[handle.node_id].append(handle)

            info.context.handle_index = handle_index

            return graphql_diagram

        except Exception as e:
            logger.error(f"Failed to get diagram {diagram_id}: {e}")
            return None

    async def list_diagrams(
        self, filter: DiagramFilterInput | None, limit: int, offset: int, info
    ) -> list[DomainDiagramType]:
        """Returns filtered diagram list."""
        try:
            # Use integrated diagram service
            integrated_service = info.context.get_service("integrated_diagram_service")

            file_infos = await integrated_service.list_diagrams()
            all_diagrams = [
                {
                    "path": fi["path"],
                    "name": fi["name"],
                    "format": fi["format"],
                    "size": fi["size"],
                    "modified": fi["modified"],
                }
                for fi in file_infos
            ]

            filtered_diagrams = all_diagrams
            if filter:
                if filter.name_contains:
                    filtered_diagrams = [
                        d
                        for d in filtered_diagrams
                        if filter.name_contains.lower() in d["name"].lower()
                    ]

                if hasattr(filter, "format") and filter.format:
                    filtered_diagrams = [
                        d for d in filtered_diagrams if d["format"] == filter.format
                    ]

                if filter.modified_after:
                    filtered_diagrams = [
                        d
                        for d in filtered_diagrams
                        if datetime.fromisoformat(d["modified"])
                        >= filter.modified_after
                    ]

                if hasattr(filter, "modified_before") and filter.modified_before:
                    filtered_diagrams = [
                        d
                        for d in filtered_diagrams
                        if datetime.fromisoformat(d["modified"])
                        <= filter.modified_before
                    ]

            start = offset
            end = offset + limit
            paginated_diagrams = filtered_diagrams[start:end]

            result = []
            for diagram_info in paginated_diagrams:
                metadata = DiagramMetadata(
                    id=diagram_info["path"],  # Use path as ID for loading
                    name=diagram_info["name"],
                    description=f"Format: {diagram_info['format']}, Size: {diagram_info['size']} bytes",
                    created=diagram_info["modified"],
                    modified=diagram_info["modified"],
                    version=DIAGRAM_VERSION,
                )

                diagram = DomainDiagram(
                    nodes=[],
                    handles=[],
                    arrows=[],
                    persons=[],
                    metadata=metadata,
                )
                # Use domain model directly
                result.append(diagram)

            return result

        except Exception as e:
            logger.error(f"Failed to list diagrams: {e}")
            return []


diagram_resolver = DiagramResolver()
