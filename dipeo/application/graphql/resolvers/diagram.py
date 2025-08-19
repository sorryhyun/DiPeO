"""Diagram resolver using ServiceRegistry."""

import logging
from typing import Optional, List

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_SERVICE
from dipeo.diagram_generated.domain_models import DiagramID, DomainDiagram
from dipeo.domain.ports.storage import DiagramInfo

from ..types.inputs import DiagramFilterInput

logger = logging.getLogger(__name__)


class DiagramResolver:
    """Resolver for diagram-related queries using service registry."""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
    
    async def get_diagram(self, id: DiagramID) -> Optional[DomainDiagram]:
        """Get a single diagram by ID."""
        try:
            service = self.registry.resolve(DIAGRAM_SERVICE)
            diagram_data = await service.get_diagram(id)
            
            # Service now returns DomainDiagram directly
            return diagram_data
            
        except FileNotFoundError:
            logger.warning(f"Diagram not found: {id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching diagram {id}: {e}")
            raise
    
    async def list_diagrams(
        self,
        filter: Optional[DiagramFilterInput] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DomainDiagram]:
        """List diagrams with optional filtering."""
        try:
            service = self.registry.resolve(DIAGRAM_SERVICE)
            
            # Get diagram metadata
            all_infos = await service.list_diagrams()
            logger.debug(f"Retrieved {len(all_infos)} diagram infos")
            
            # Apply filters if provided
            filtered_infos = all_infos
            if filter:
                filtered_infos = [
                    info for info in all_infos
                    if self._matches_info_filter(info, filter)
                ]
            
            # Apply pagination
            paginated_infos = filtered_infos[offset:offset + limit]
            
            # Load full diagrams for the paginated results
            diagrams = []
            for info in paginated_infos:
                try:
                    diagram = await service.get_diagram(info.id)
                    if diagram:
                        diagrams.append(diagram)
                except Exception as e:
                    logger.warning(f"Failed to load diagram {info.id}: {e}")
                    continue
            
            return diagrams
            
        except Exception as e:
            import traceback
            logger.error(f"Error listing diagrams: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _matches_info_filter(self, info: DiagramInfo, filter: DiagramFilterInput) -> bool:
        """Check if diagram info matches the filter criteria."""
        # Extract name from path if metadata not available
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
        
        # Date filters can use info.created and info.modified
        # TODO: Add date filtering logic if needed
        
        return True