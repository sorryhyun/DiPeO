#!/usr/bin/env python3
"""Export GraphQL schema from the server."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up minimal environment
os.environ.setdefault('LOG_LEVEL', 'ERROR')

# Import after path setup
from dipeo_server.api.graphql.schema import unified_schema

if __name__ == "__main__":
    schema_str = unified_schema.as_str()
    
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
        with open(output_path, 'w') as f:
            f.write(schema_str)
        print(f"Schema exported to {output_path}", file=sys.stderr)
    else:
        print(schema_str)