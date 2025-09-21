"""Diagram resolver using ServiceRegistry."""

import logging

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_PORT
from dipeo.diagram_generated.domain_models import DiagramID, DomainDiagram
from dipeo.diagram_generated.graphql.inputs import DiagramFilterInput
from dipeo.domain.base.storage_port import DiagramInfo

logger = logging.getLogger(__name__)


class DiagramResolver:
    """Resolver for diagram-related queries using service registry."""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry

    async def get_diagram(self, id: DiagramID) -> DomainDiagram | None:
        try:
            service = self.registry.resolve(DIAGRAM_PORT)
            diagram_data = await service.get_diagram(id)
            return diagram_data

        except FileNotFoundError:
            logger.warning(f"Diagram not found: {id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching diagram {id}: {e}")
            raise

    async def list_diagrams(
        self, filter: DiagramFilterInput | None = None, limit: int = 100, offset: int = 0
    ) -> list[DomainDiagram]:
        try:
            service = self.registry.resolve(DIAGRAM_PORT)
            all_infos = await service.list_diagrams()
            logger.debug(f"Retrieved {len(all_infos)} diagram infos")

            filtered_infos = all_infos
            if filter:
                filtered_infos = [
                    info for info in all_infos if self._matches_info_filter(info, filter)
                ]

            paginated_infos = filtered_infos[offset : offset + limit]
            diagrams = []
            for info in paginated_infos:
                try:
                    diagram = await service.get_diagram(info.id)
                    if diagram:
                        diagrams.append(diagram)
                except Exception as e:
                    logger.warning(f"Failed to load diagram {info.id}: {e}")
                    # Create a minimal diagram with metadata from DiagramInfo
                    # This allows the UI to at least show the file exists
                    from pathlib import Path

                    from dipeo.diagram_generated import DiagramMetadata, DomainDiagram

                    # Extract name from path if not in metadata
                    name = None
                    if info.metadata and "name" in info.metadata:
                        name = info.metadata["name"]
                    elif info.path:
                        name = Path(info.path).stem

                    from datetime import datetime

                    # Get timestamp for created/modified
                    now_str = datetime.now().isoformat()

                    try:
                        minimal_diagram = DomainDiagram(
                            nodes=[],  # Empty nodes list
                            arrows=[],  # Empty arrows list
                            handles=[],  # Empty handles list
                            persons=[],  # Empty persons list - REQUIRED FIELD
                            metadata=DiagramMetadata(
                                id=info.id,
                                name=name or info.id,
                                description=f"Failed to load: {str(e)[:100]}",  # Include error info
                                version="1.0",  # Default version
                                created=str(info.created) if info.created else now_str,
                                modified=str(info.modified) if info.modified else now_str,
                            ),
                        )
                        diagrams.append(minimal_diagram)
                    except Exception as fallback_error:
                        # If we can't even create a minimal diagram, just skip this one entirely
                        logger.error(
                            f"Failed to create minimal diagram for {info.id}: {fallback_error}"
                        )
                        # Continue to next diagram without adding anything to the list
                        continue

            return diagrams

        except Exception as e:
            import traceback

            logger.error(f"Error listing diagrams: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def _matches_info_filter(self, info: DiagramInfo, filter: DiagramFilterInput) -> bool:
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
