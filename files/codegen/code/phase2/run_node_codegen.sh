#!/bin/bash
# Script to run node UI code generation

set -e  # Exit on error

# Get the project root from environment or use default
PROJECT_ROOT="${DIPEO_BASE_DIR:-/home/soryhyun/DiPeO}"
cd "$PROJECT_ROOT"

# Get node spec path from inputs or use default
NODE_SPEC="${1:-files/specifications/nodes/typescript_ast_parser.json}"

echo "Running node UI code generation..."
echo "Working directory: $(pwd)"
echo "Node specification: $NODE_SPEC"

# Check if spec file exists
if [ ! -f "$NODE_SPEC" ]; then
    echo "Error: Node specification file not found: $NODE_SPEC"
    exit 1
fi

# Run the main codegen diagram
echo ""
echo "Executing node codegen diagram..."
dipeo run codegen/node_ui_codegen --light --no-browser --timeout=30 --vars "node_spec_path=$NODE_SPEC"

# Note: In a real implementation, we would parse the spec file
# and generate appropriate UI components. For now, we'll list
# expected output files.

echo ""
echo "Expected generated files for node UI:"
echo "  - apps/web/src/__generated__/nodes/TypescriptAstNode.tsx"
echo "  - apps/server/src/dipeo_server/api/graphql/schema/nodes/typescript_ast.graphql"
echo "  - apps/web/src/__generated__/fields/typescriptAstFields.ts"

echo ""
echo "Node UI generation completed"