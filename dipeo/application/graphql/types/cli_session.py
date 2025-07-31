"""CLI session types for GraphQL schema."""

import strawberry
from typing import Optional
from datetime import datetime

# No need to import ExecutableDiagram since we store data as JSON string


@strawberry.type
class CliSession:
    """Represents an active CLI execution session."""
    
    execution_id: str
    diagram_name: str
    diagram_format: str
    started_at: datetime
    is_active: bool
    diagram_data: Optional[str] = None  # Serialized diagram for browser
    
    @strawberry.field
    def session_id(self) -> str:
        """Unique session identifier."""
        return f"cli_{self.execution_id}"