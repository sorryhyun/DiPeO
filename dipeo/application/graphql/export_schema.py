"""Export complete GraphQL schema from application layer."""

import sys
from pathlib import Path

from dipeo.application.graphql import create_schema
from dipeo.application.registry import ServiceRegistry


def export_schema(output_path: str | None = None) -> str:
    """Export the GraphQL schema as a string."""
    registry = ServiceRegistry()
    schema = create_schema(registry)
    schema_str = schema.as_str()

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(schema_str)
        print(f"GraphQL schema exported to {output_path}", file=sys.stderr)
        print(f"Schema length: {len(schema_str)} characters", file=sys.stderr)

    return schema_str


if __name__ == "__main__":
    output_path = sys.argv[1] if len(sys.argv) > 1 else None

    if output_path:
        export_schema(output_path)
    else:
        print(export_schema())
