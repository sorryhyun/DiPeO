#!/bin/bash
# Script to run domain model code generation

set -e  # Exit on error

# Get the project root from environment or use default
PROJECT_ROOT="${DIPEO_BASE_DIR:-/home/soryhyun/DiPeO}"
cd "$PROJECT_ROOT"

echo "=== DOMAIN MODEL CODEGEN START ==="
echo "Running domain model code generation..."
echo "Working directory: $(pwd)"
echo "Script running as user: $(whoami)"
echo "Current time: $(date)"

# Run make codegen command
make codegen 2>&1

# Check results and list generated files
echo ""
echo "Generated files:"
ls -la dipeo/models/models.py 2>/dev/null && echo "  - dipeo/models/models.py"
ls -la dipeo/models/conversions.py 2>/dev/null && echo "  - dipeo/models/conversions.py"
ls -la dipeo/core/static/generated_nodes.py 2>/dev/null && echo "  - dipeo/core/static/generated_nodes.py"
ls -la apps/web/src/__generated__/graphql.tsx 2>/dev/null && echo "  - apps/web/src/__generated__/graphql.tsx"

# Return success with file list
echo ""
echo "Domain model generation completed successfully"