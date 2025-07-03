#!/bin/bash
# Pre-build script for Vercel deployment
# Ensures GraphQL schema is available for codegen

# Copy the GraphQL schema to the expected location
if [ -f "../server/schema.graphql" ]; then
  echo "Schema found at ../server/schema.graphql"
elif [ -f "../../apps/server/schema.graphql" ]; then
  echo "Copying schema from ../../apps/server/schema.graphql"
  mkdir -p ../server
  cp ../../apps/server/schema.graphql ../server/schema.graphql
else
  echo "ERROR: Could not find schema.graphql"
  exit 1
fi

echo "Pre-build setup complete"