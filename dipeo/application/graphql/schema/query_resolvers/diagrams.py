"""Diagram-related query resolvers."""

import logging
from datetime import datetime
from pathlib import Path

import strawberry

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_PORT
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import DiagramMetadata, DomainDiagram
from dipeo.diagram_generated.domain_models import DiagramID
from dipeo.diagram_generated.graphql.domain_types import DomainDiagramType
from dipeo.diagram_generated.graphql.inputs import DiagramFilterInput

logger = get_module_logger(__name__)


async def get_diagram(
    registry: ServiceRegistry, diagram_id: strawberry.ID
) -> DomainDiagramType | None:
    """Get a single diagram by ID."""
    try:
        service = registry.resolve(DIAGRAM_PORT)
        diagram_id_typed = DiagramID(str(diagram_id))
        diagram_data = await service.get_diagram(diagram_id_typed)
        return diagram_data
    except FileNotFoundError:
        logger.warning(f"Diagram not found: {diagram_id}")
        return None
    except Exception as e:
        logger.error(f"Error fetching diagram {diagram_id}: {e}")
        raise


async def list_diagrams(
    registry: ServiceRegistry,
    filter: DiagramFilterInput | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[DomainDiagramType]:
    """List diagrams with optional filtering."""
    try:
        service = registry.resolve(DIAGRAM_PORT)
        all_infos = await service.list_diagrams()
        logger.debug(f"Retrieved {len(all_infos)} diagram infos")

        filtered_infos = all_infos
        if filter:
            filtered_infos = [info for info in all_infos if _matches_diagram_filter(info, filter)]

        paginated_infos = filtered_infos[offset : offset + limit]
        diagrams = []
        for info in paginated_infos:
            try:
                diagram = await service.get_diagram(info.id)
                if diagram:
                    diagrams.append(diagram)
            except Exception as e:
                logger.warning(f"Failed to load diagram {info.id}: {e}")

                name = None
                if info.metadata and "name" in info.metadata:
                    name = info.metadata["name"]
                elif info.path:
                    name = Path(info.path).stem

                now_str = datetime.now().isoformat()

                try:
                    minimal_diagram = DomainDiagram(
                        nodes=[],
                        arrows=[],
                        handles=[],
                        persons=[],
                        metadata=DiagramMetadata(
                            id=info.id,
                            name=name or info.id,
                            description=f"Failed to load: {str(e)[:100]}",
                            version="1.0",
                            created=str(info.created) if info.created else now_str,
                            modified=str(info.modified) if info.modified else now_str,
                        ),
                    )
                    diagrams.append(minimal_diagram)
                except Exception as fallback_error:
                    logger.error(
                        f"Failed to create minimal diagram for {info.id}: {fallback_error}"
                    )
                    continue

        return diagrams

    except Exception as e:
        import traceback

        logger.error(f"Error listing diagrams: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


def _matches_diagram_filter(info, filter: DiagramFilterInput) -> bool:
    """Check if a DiagramInfo matches filter criteria."""
    name = ""
    if info.metadata and "name" in info.metadata:
        name = info.metadata["name"]
    elif info.path:
        name = info.path.stem

    if filter.name and filter.name.lower() not in name.lower():
        return False

    if filter.author:
        author = info.metadata.get("author", "") if info.metadata else ""
        if filter.author != author:
            return False

    if filter.tags:
        tags = info.metadata.get("tags", []) if info.metadata else []
        if not any(tag in tags for tag in filter.tags):
            return False

    return True
