"""GraphQL resolvers for diagram operations."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

from dipeo_domain import DiagramDictFormat

from dipeo_server.domains.diagram import DiagramService
from dipeo_server.domains.diagram.converters import diagram_dict_to_graphql

from .domain_types import DiagramMetadata, DomainDiagramType
from .inputs_types import DiagramFilterInput
from .scalars_types import DiagramID

logger = logging.getLogger(__name__)


class DiagramResolver:
    """Handles diagram queries and data retrieval."""

    async def get_diagram(
        self, diagram_id: DiagramID, info
    ) -> Optional[DomainDiagramType]:
        """Returns diagram by ID."""
        try:
            logger.info(f"Attempting to get diagram with ID: {diagram_id}")
            diagram_service: DiagramService = info.context.diagram_service

            diagram_data = await diagram_service.get_diagram(diagram_id)

            if not diagram_data:
                logger.error(f"Diagram not found: {diagram_id}")
                return None

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
                    "created": diagram_data.get("created", datetime.now().isoformat()),
                    "modified": diagram_data.get(
                        "modified", datetime.now().isoformat()
                    ),
                }

            diagram_dict = DiagramDictFormat.model_validate(diagram_data)
            graphql_diagram = diagram_dict_to_graphql(diagram_dict)

            handle_index = defaultdict(list)
            for handle in graphql_diagram.handles:
                handle_index[handle.node_id].append(handle)

            info.context.handle_index = handle_index

            return DomainDiagramType(
                nodes=graphql_diagram.nodes,
                handles=graphql_diagram.handles,
                arrows=graphql_diagram.arrows,
                persons=graphql_diagram.persons,
                api_keys=graphql_diagram.api_keys,
                metadata=graphql_diagram.metadata,
            )

        except Exception as e:
            logger.error(f"Failed to get diagram {diagram_id}: {e}")
            return None

    async def list_diagrams(
        self, filter: Optional[DiagramFilterInput], limit: int, offset: int, info
    ) -> List[DomainDiagramType]:
        """Returns filtered diagram list."""
        try:
            diagram_service: DiagramService = info.context.diagram_service

            all_diagrams = diagram_service.list_diagram_files()

            filtered_diagrams = all_diagrams
            if filter:
                if filter.name:
                    filtered_diagrams = [
                        d
                        for d in filtered_diagrams
                        if filter.name.lower() in d["name"].lower()
                    ]

                if filter.format:
                    filtered_diagrams = [
                        d for d in filtered_diagrams if d["format"] == filter.format
                    ]

                if filter.modifiedAfter:
                    filtered_diagrams = [
                        d
                        for d in filtered_diagrams
                        if datetime.fromisoformat(d["modified"]) >= filter.modifiedAfter
                    ]

                if filter.modifiedBefore:
                    filtered_diagrams = [
                        d
                        for d in filtered_diagrams
                        if datetime.fromisoformat(d["modified"])
                        <= filter.modifiedBefore
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
                    created=datetime.fromisoformat(diagram_info["modified"]),
                    modified=datetime.fromisoformat(diagram_info["modified"]),
                    version="2.0.0",
                )

                diagram = DomainDiagramType(
                    nodes=[],
                    handles=[],
                    arrows=[],
                    persons=[],
                    api_keys=[],
                    metadata=metadata,
                )
                result.append(diagram)

            return result

        except Exception as e:
            logger.error(f"Failed to list diagrams: {e}")
            return []


diagram_resolver = DiagramResolver()
