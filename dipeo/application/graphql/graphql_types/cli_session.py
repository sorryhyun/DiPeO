"""CLI session types for GraphQL schema."""

from datetime import datetime

import strawberry
from strawberry.scalars import JSON

# No need to import ExecutableDiagram since we store data as JSON string


@strawberry.type
class CliSession:
    """Represents an active CLI execution session."""

    execution_id: str
    diagram_name: str
    diagram_format: str
    started_at: datetime
    is_active: bool
    diagram_data: str | None = None  # Serialized diagram for browser
    node_states: JSON | None = None  # Initial node states for immediate highlighting

    @strawberry.field
    def session_id(self) -> str:
        """Unique session identifier."""
        return f"cli_{self.execution_id}"
