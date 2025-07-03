#!/bin/bash

# Build script to ensure proper generation sequence
# This ensures packages/domain-models is the single source of truth

set -e

echo "🔨 Building DiPeO with proper dependency order..."

# 1. Build domain models and generate all derived code
echo "📦 Building domain models..."
cd packages/domain-models
pnpm install
pnpm build  # This runs TypeScript compilation and all generators

# 2. Install all Python packages from requirements.txt
echo "🐍 Installing Python packages..."
cd ../..
pip install -r requirements.txt

# 3. Now install the server (which depends on dipeo_domain)
echo "🚀 Installing server..."
cd apps/server
pip install -e .

# 4. Generate GraphQL schema from the server
echo "📝 Exporting GraphQL schema..."
python -c "
from dipeo_server.api.graphql.schema import schema
schema_str = schema.as_str()
with open('schema.graphql', 'w') as f:
    f.write(schema_str)
print(f'✅ GraphQL schema exported ({len(schema_str)} characters)')
"

# 5. Run GraphQL codegen for frontend
echo "🎨 Running GraphQL codegen..."
cd ../web
pnpm install
pnpm run codegen

echo "✅ Build complete! All components are properly synchronized."