#!/bin/bash
# Export GraphQL schema to frontend
SCHEMA_PATH="apps/web/src/schema.graphql"
mkdir -p apps/web/src
python -m apps.server.src.graphql.export_schema "$SCHEMA_PATH"
echo "Schema exported to: $SCHEMA_PATH"