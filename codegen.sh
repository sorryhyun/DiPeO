#!/bin/bash

# GraphQL Code Generation Script for DiPeO
# This script exports the GraphQL schema from the server and generates TypeScript types for the frontend

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

print_status "Starting GraphQL schema export process..."

# Step 1: Export schema from server
print_status "Exporting schema from server..."
cd server
python -m src.interfaces.graphql.schema ../web/schema.graphql
if [ $? -eq 0 ]; then
    print_status "Schema exported successfully to web/schema.graphql"
else
    print_error "Failed to export schema"
    exit 1
fi
cd ..

# Step 2: Run codegen
print_status "Running GraphQL codegen..."
pnpm codegen
if [ $? -eq 0 ]; then
    print_status "Codegen completed successfully"
else
    print_error "Failed to run codegen"
    exit 1
fi

print_status "GraphQL schema export and codegen completed successfully!"
print_status "Generated files are in: web/src/__generated__/"

# Optional: Start the development server if --dev flag is provided
if [[ "$1" == "--dev" ]]; then
    print_status "Starting frontend development server..."
    pnpm dev
else
    print_status "Run 'pnpm dev' to start the frontend development server"
    print_status "Or use './dev.sh --frontend' to start the frontend"
fi