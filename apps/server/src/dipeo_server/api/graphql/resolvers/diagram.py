"""GraphQL resolvers for diagram operations."""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional

import yaml
from dipeo_domain import DiagramMetadata, DomainDiagram

from dipeo_server.domains.diagram.converters import (
    backend_to_graphql,
    converter_registry,
    graphql_to_backend,
)
from dipeo_server.domains.diagram.services import DiagramStorageService
from dipeo_server.domains.diagram.services.models import BackendDiagram

from ..types import (
    DiagramFilterInput,
    DiagramID,
    DomainDiagramType,
)

logger = logging.getLogger(__name__)


class DiagramResolver:
    """Handles diagram queries and data retrieval."""

    async def get_diagram(
        self, diagram_id: DiagramID, info
    ) -> Optional[DomainDiagramType]:
        """Returns diagram by ID."""
        try:
            logger.info(f"Attempting to get diagram with ID: {diagram_id}")

            # Try new services first
            storage_service: DiagramStorageService = (
                info.context.diagram_storage_service
            )

            # Find and load the diagram
            path = await storage_service.find_by_id(diagram_id)
            if not path:
                logger.error(f"Diagram not found: {diagram_id}")
                return None

            diagram_data = await storage_service.read_file(path)

            if not diagram_data:
                logger.error(f"Diagram not found: {diagram_id}")
                return None

            # Determine format from path
            from pathlib import Path

            path_obj = Path(path)
            format_from_path = storage_service._determine_format_type(path_obj)

            # Check if this is a light format diagram (from path or has version: light)
            if format_from_path == "light" or diagram_data.get("version") == "light":
                logger.info(f"Detected light format for diagram {diagram_id}")

                # Ensure api_keys is present as an empty list if not provided
                if "api_keys" not in diagram_data:
                    diagram_data["api_keys"] = []

                # Convert the data to YAML string for converter processing
                yaml_content = yaml.dump(diagram_data, default_flow_style=False)

                # Use the converter to deserialize from light format
                graphql_diagram = converter_registry.deserialize(yaml_content, "light")

                # Update metadata if needed
                if not graphql_diagram.metadata or not graphql_diagram.metadata.id:
                    graphql_diagram.metadata = DiagramMetadata(
                        id=diagram_id,
                        name=diagram_id.replace("/", " - ")
                        .replace(".yaml", "")
                        .replace(".yml", "")
                        .replace(".json", "")
                        .replace("_", " ")
                        .title(),
                        description="Light format diagram",
                        version="light",
                        created=datetime.now(timezone.utc).isoformat(),
                        modified=datetime.now(timezone.utc).isoformat(),
                    )
            else:
                # Original handling for non-light formats
                if "metadata" not in diagram_data or not diagram_data["metadata"]:
                    diagram_data["metadata"] = {
                        "id": diagram_id,
                        "name": diagram_id.replace("/", " - ")
                        .replace(".yaml", "")
                        .replace(".yml", "")
                        .replace(".json", "")
                        .replace("_", " ")
                        .title(),
                        "description": diagram_data.get("description", ""),
                        "version": diagram_data.get("version", "2.0.0"),
                        "created": diagram_data.get(
                            "created", datetime.now(timezone.utc).isoformat()
                        ),
                        "modified": diagram_data.get(
                            "modified", datetime.now(timezone.utc).isoformat()
                        ),
                    }

                # Check if the data is in native format (lists) or backend format (dicts)
                if isinstance(diagram_data.get("nodes", {}), list):
                    # Native format - parse as DomainDiagram first, then convert to BackendDiagram
                    domain_diagram = DomainDiagram(**diagram_data)
                    diagram_dict = graphql_to_backend(domain_diagram)
                    graphql_diagram = domain_diagram
                else:
                    # Backend format - parse directly as BackendDiagram
                    diagram_dict = BackendDiagram(**diagram_data)
                    graphql_diagram = backend_to_graphql(diagram_dict)

            handle_index = defaultdict(list)
            for handle in graphql_diagram.handles:
                handle_index[handle.node_id].append(handle)

            info.context.handle_index = handle_index

            return graphql_diagram

        except Exception as e:
            logger.error(f"Failed to get diagram {diagram_id}: {e}")
            return None

    async def list_diagrams(
        self, filter: Optional[DiagramFilterInput], limit: int, offset: int, info
    ) -> List[DomainDiagramType]:
        """Returns filtered diagram list."""
        try:
            # Use new storage service
            storage_service: DiagramStorageService = (
                info.context.diagram_storage_service
            )

            file_infos = await storage_service.list_files()
            all_diagrams = [
                {
                    "path": fi.path,
                    "name": fi.name,
                    "format": fi.format,
                    "size": fi.size,
                    "modified": fi.modified,
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
                    version="2.0.0",
                )

                diagram = DomainDiagram(
                    nodes=[],
                    handles=[],
                    arrows=[],
                    persons=[],
                    apiKeys=[],
                    metadata=metadata,
                )
                result.append(diagram)

            return result

        except Exception as e:
            logger.error(f"Failed to list diagrams: {e}")
            return []


diagram_resolver = DiagramResolver()
