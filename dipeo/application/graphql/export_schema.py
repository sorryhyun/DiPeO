"""Export complete GraphQL schema from application layer.

This module exports the complete GraphQL schema without requiring the server layer,
allowing frontend codegen to work directly from the application layer schema.
"""

import sys
from pathlib import Path

from dipeo.application.graphql import create_schema
from dipeo.application.registry import ServiceRegistry


def export_schema(output_path: str = None) -> str:
    """Export the complete GraphQL schema.
    
    Args:
        output_path: Optional file path to write schema to
        
    Returns:
        The GraphQL schema as a string
    """
    # Create mock registry for schema export
    registry = ServiceRegistry()
    
    # Create and export schema
    schema = create_schema(registry)
    schema_str = schema.as_str()
    
    # Write to file if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(schema_str)
        print(f"GraphQL schema exported to {output_path}", file=sys.stderr)
        print(f"Schema length: {len(schema_str)} characters", file=sys.stderr)
    
    return schema_str


if __name__ == "__main__":
    # Support command line usage
    output_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if output_path:
        export_schema(output_path)
    else:
        # Print to stdout for piping
        print(export_schema())