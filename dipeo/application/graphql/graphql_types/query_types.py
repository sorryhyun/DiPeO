"""GraphQL query-specific types for DiPeO."""

import strawberry


@strawberry.type
class DiagramFormatInfo:
    """Information about a supported diagram format."""

    format: str
    name: str
    extension: str
    supports_export: bool
    supports_import: bool
    description: str | None = None
