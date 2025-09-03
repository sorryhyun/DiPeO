"""Service for managing CLI execution sessions."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import json
import logging
import yaml
from dataclasses import dataclass

from dipeo.infrastructure.diagram.adapters import UnifiedSerializerAdapter


@dataclass
class CliSessionData:
    """Internal representation of a CLI session."""
    execution_id: str
    diagram_name: str
    diagram_format: str
    started_at: datetime
    is_active: bool
    diagram_data: Optional[str] = None


logger = logging.getLogger(__name__)


class CliSessionService:
    """Manages active CLI execution sessions."""
    
    def __init__(self):
        self._active_session: Optional[CliSessionData] = None
        self._lock = asyncio.Lock()
        
    async def start_cli_session(
        self, 
        execution_id: str,
        diagram_name: str,
        diagram_format: str,
        diagram_data: Optional[Dict[str, Any]] = None
    ) -> CliSessionData:
        """Start a new CLI session."""
        async with self._lock:
            # Only one CLI session can be active at a time
            if self._active_session and self._active_session.is_active:
                logger.warning(f"Ending previous CLI session {self._active_session.execution_id}")
                self._active_session.is_active = False
            
            # Check if diagram data needs conversion or is already in frontend format
            converted_data = diagram_data
            
            # If diagram_data has 'nodes' as a list, it's already in frontend format
            if diagram_data and isinstance(diagram_data.get('nodes'), list):
                # Already in frontend-compatible format, no conversion needed
                converted_data = diagram_data
            elif diagram_data and diagram_format == "light":
                # Only convert if it's actually in light format (not already converted)
                try:
                    # Create serializer adapter
                    serializer = UnifiedSerializerAdapter()
                    await serializer.initialize()
                    
                    # Convert to YAML string then deserialize to DomainDiagram
                    yaml_content = yaml.dump(diagram_data, default_flow_style=False)
                    domain_diagram = serializer.deserialize_from_storage(yaml_content, format="light")
                    
                    # Convert to frontend-compatible format (arrays, not objects)
                    converted_data = {
                        "nodes": [node.model_dump(by_alias=True) for node in domain_diagram.nodes],
                        "handles": [handle.model_dump(by_alias=True) for handle in domain_diagram.handles],
                        "arrows": [
                            {
                                **arrow.model_dump(by_alias=True, exclude={"content_type"}),
                                "content_type": arrow.content_type.value if arrow.content_type and hasattr(arrow.content_type, "value") else str(arrow.content_type) if arrow.content_type else None
                            } 
                            for arrow in domain_diagram.arrows
                        ],
                        "persons": [person.model_dump(by_alias=True) for person in domain_diagram.persons],
                    }
                    
                    if domain_diagram.metadata:
                        converted_data["metadata"] = domain_diagram.metadata.model_dump(by_alias=True)
                    
                except Exception as e:
                    logger.error(f"Failed to convert diagram format: {e}")
                    # Fall back to original data
                    converted_data = diagram_data
            
            # Create new session
            self._active_session = CliSessionData(
                execution_id=execution_id,
                diagram_name=diagram_name,
                diagram_format=diagram_format,
                started_at=datetime.utcnow(),
                is_active=True,
                diagram_data=json.dumps(converted_data) if converted_data else None
            )
            
            return self._active_session
    
    async def end_cli_session(self, execution_id: str) -> bool:
        """End a CLI session."""
        async with self._lock:
            if self._active_session and self._active_session.execution_id == execution_id:
                self._active_session.is_active = False
                logger.info(f"Ended CLI session for execution {execution_id}")
                return True
            return False
    
    async def get_active_session(self) -> Optional[CliSessionData]:
        """Get the current active CLI session."""
        async with self._lock:
            if self._active_session and self._active_session.is_active:
                return self._active_session
            return None
    
    async def clear_inactive_sessions(self):
        """Clear any inactive sessions."""
        async with self._lock:
            if self._active_session and not self._active_session.is_active:
                self._active_session = None