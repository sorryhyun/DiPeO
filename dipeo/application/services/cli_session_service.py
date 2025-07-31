"""Service for managing CLI execution sessions."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import json
import logging

from dipeo.application.graphql.types.cli_session import CliSession
# Import removed - diagram data is stored as JSON


logger = logging.getLogger(__name__)


class CliSessionService:
    """Manages active CLI execution sessions."""
    
    def __init__(self):
        self._active_session: Optional[CliSession] = None
        self._lock = asyncio.Lock()
        
    async def start_cli_session(
        self, 
        execution_id: str,
        diagram_name: str,
        diagram_format: str,
        diagram_data: Optional[Dict[str, Any]] = None
    ) -> CliSession:
        """Start a new CLI session."""
        async with self._lock:
            # Only one CLI session can be active at a time
            if self._active_session and self._active_session.is_active:
                logger.warning(f"Ending previous CLI session {self._active_session.execution_id}")
                self._active_session.is_active = False
            
            # Create new session
            self._active_session = CliSession(
                execution_id=execution_id,
                diagram_name=diagram_name,
                diagram_format=diagram_format,
                started_at=datetime.utcnow(),
                is_active=True,
                diagram_data=json.dumps(diagram_data) if diagram_data else None
            )
            
            logger.info(f"Started CLI session for execution {execution_id}")
            return self._active_session
    
    async def end_cli_session(self, execution_id: str) -> bool:
        """End a CLI session."""
        async with self._lock:
            if self._active_session and self._active_session.execution_id == execution_id:
                self._active_session.is_active = False
                logger.info(f"Ended CLI session for execution {execution_id}")
                return True
            return False
    
    async def get_active_session(self) -> Optional[CliSession]:
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