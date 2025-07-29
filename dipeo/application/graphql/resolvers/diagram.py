"""Diagram resolver using UnifiedServiceRegistry."""

import logging
from typing import Optional, List

from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey
from dipeo.diagram_generated.domain_models import DiagramID, DomainDiagram
from dipeo.domain.diagram.utils import dict_to_domain_diagram

from ..types.inputs import DiagramFilterInput

logger = logging.getLogger(__name__)

# Service keys
INTEGRATED_DIAGRAM_SERVICE = ServiceKey("integrated_diagram_service")


class DiagramResolver:
    """Resolver for diagram-related queries using service registry."""
    
    def __init__(self, registry: UnifiedServiceRegistry):
        self.registry = registry
    
    async def get_diagram(self, id: DiagramID) -> Optional[DomainDiagram]:
        """Get a single diagram by ID."""
        try:
            service = self.registry.require(INTEGRATED_DIAGRAM_SERVICE)
            diagram_data = await service.get_diagram(id)
            
            if not diagram_data:
                return None
            
            # Ensure diagram_data is a dict before conversion
            if not isinstance(diagram_data, dict):
                logger.error(f"Diagram {id} returned non-dict data: {type(diagram_data)}")
                return None
                
            # Convert to domain model
            domain_diagram = dict_to_domain_diagram(diagram_data)
            return domain_diagram
            
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
            service = self.registry.require(INTEGRATED_DIAGRAM_SERVICE)
            
            # Get all diagram infos
            diagram_infos = await service.list_diagrams()
            
            # Debug log to check what we're getting
            if diagram_infos and len(diagram_infos) > 0:
                logger.debug(f"First diagram info type: {type(diagram_infos[0])}")
                # Log any non-dict entries for debugging
                for idx, info in enumerate(diagram_infos[:5]):  # Check first 5 entries
                    if not isinstance(info, dict):
                        logger.debug(f"Entry {idx} is {type(info)}: {info!r}")
            
            # Filter out non-dict entries first
            valid_infos = [
                info for info in diagram_infos
                if isinstance(info, dict)
            ]
            
            # Log if we found non-dict entries
            invalid_count = len(diagram_infos) - len(valid_infos)
            if invalid_count > 0:
                logger.warning(f"Found {invalid_count} non-dict entries in diagram list")
            
            # Apply filters if provided
            filtered_infos = valid_infos
            if filter:
                filtered_infos = [
                    info for info in valid_infos
                    if self._matches_filter(info, filter)
                ]
            
            # Apply pagination
            paginated_infos = filtered_infos[offset:offset + limit]
            
            # Load full diagrams
            diagrams = []
            for info in paginated_infos:
                diagram_id = info.get("id") or info.get("path", "").split(".")[0]
                if diagram_id:
                    try:
                        diagram_data = await service.get_diagram(diagram_id)
                        if diagram_data:
                            # Ensure diagram_data is a dict
                            if not isinstance(diagram_data, dict):
                                logger.warning(f"Diagram {diagram_id} returned non-dict data: {type(diagram_data)}")
                                continue
                            domain_diagram = dict_to_domain_diagram(diagram_data)
                            diagrams.append(domain_diagram)
                    except (KeyError, ValueError) as e:
                        # Skip diagrams that fail to load
                        logger.warning(f"Skipping diagram {diagram_id}: {e}")
                        continue
            
            return diagrams
            
        except Exception as e:
            import traceback
            logger.error(f"Error listing diagrams: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _matches_filter(self, info: dict, filter: DiagramFilterInput) -> bool:
        """Check if a diagram info matches the filter criteria."""
        # Ensure info is a dict
        if not isinstance(info, dict):
            return False
            
        if filter.name and filter.name.lower() not in info.get("name", "").lower():
            return False
        
        if filter.author and filter.author != info.get("author", ""):
            return False
        
        if filter.tags:
            diagram_tags = info.get("tags", [])
            if not any(tag in diagram_tags for tag in filter.tags):
                return False
        
        # Date filters would need metadata from full diagram
        # Skip for now as it requires loading full diagram
        
        return True