#!/bin/bash
# Export GraphQL schema to frontend
SCHEMA_PATH="web/src/schema.graphql"
mkdir -p web/src
python -m server.src.graphql.export_schema "$SCHEMA_PATH"
echo "Schema exported to: $SCHEMA_PATH"