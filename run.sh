#!/bin/bash

# Quick start script for DiPeO
# This script provides a simple way to start the application

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Show banner
echo "╔══════════════════════════════════════╗"
echo "║          DiPeO Quick Start           ║"
echo "╚══════════════════════════════════════╝"
echo

# Check if this is first run (no node_modules)
if [ ! -d "node_modules" ]; then
    print_info "First time setup detected. Installing dependencies..."
    pnpm install
    print_success "Dependencies installed"
    
    print_info "Running initial code generation..."
    ./dev.sh --generate
    print_success "Code generation completed"
fi

# Start services based on argument
case "${1:-all}" in
    frontend|f)
        print_info "Starting frontend only..."
        ./dev.sh --frontend
        ;;
    backend|b)
        print_info "Starting backend only..."
        ./dev.sh --backend
        ;;
    all|a|"")
        print_info "Starting both frontend and backend..."
        ./dev.sh --all
        ;;
    *)
        echo "Usage: $0 [frontend|backend|all]"
        echo "  frontend (f) - Start only the frontend"
        echo "  backend (b)  - Start only the backend"
        echo "  all (a)      - Start both (default)"
        exit 1
        ;;
esac