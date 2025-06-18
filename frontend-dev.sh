#!/bin/bash

# DiPeO Frontend Development Script
# This script automates the frontend development workflow

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if we're in the project root
if [ ! -f "package.json" ] || [ ! -d "web" ]; then
    print_error "This script must be run from the DiPeO project root"
    exit 1
fi

# Parse command line arguments
SKIP_INSTALL=false
SKIP_SERVER=false
SKIP_CODEGEN=false
WATCH_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        --skip-server)
            SKIP_SERVER=true
            shift
            ;;
        --skip-codegen)
            SKIP_CODEGEN=true
            shift
            ;;
        --watch)
            WATCH_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --skip-install   Skip pnpm install step"
            echo "  --skip-server    Skip backend server startup"
            echo "  --skip-codegen   Skip GraphQL codegen"
            echo "  --watch          Run in watch mode (keeps running)"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for server to be ready
wait_for_server() {
    local port=$1
    local max_attempts=30
    local attempt=0
    
    print_info "Waiting for server on port $port to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if check_port $port; then
            # Additional check for GraphQL endpoint
            if curl -s -X POST http://localhost:$port/graphql \
                -H "Content-Type: application/json" \
                -d '{"query":"{ __typename }"}' >/dev/null 2>&1; then
                print_success "Server is ready!"
                return 0
            fi
        fi
        
        attempt=$((attempt + 1))
        sleep 1
        echo -n "."
    done
    
    echo
    print_error "Server failed to start within 30 seconds"
    return 1
}

# Step 1: Install dependencies
if [ "$SKIP_INSTALL" = false ]; then
    print_info "Installing dependencies..."
    pnpm install
    print_success "Dependencies installed"
else
    print_info "Skipping dependency installation"
fi

# Step 2: Start backend server if needed
BACKEND_PID=""
if [ "$SKIP_SERVER" = false ]; then
    if ! check_port 8000; then
        print_info "Starting backend server..."
        cd server
        python main.py > ../logs/backend.log 2>&1 &
        BACKEND_PID=$!
        cd ..
        
        # Wait for server to be ready
        if ! wait_for_server 8000; then
            print_error "Failed to start backend server"
            if [ ! -z "$BACKEND_PID" ]; then
                kill $BACKEND_PID 2>/dev/null
            fi
            exit 1
        fi
    else
        print_warning "Backend server already running on port 8000"
    fi
else
    print_info "Skipping backend server startup"
fi

# Step 3: Download schema if server is available
if check_port 8000 && [ "$SKIP_CODEGEN" = false ]; then
    print_info "Downloading GraphQL schema..."
    cd web
    if pnpm download-schema; then
        print_success "Schema downloaded successfully"
    else
        print_warning "Failed to download schema, continuing anyway..."
    fi
    cd ..
fi

# Step 4: Generate GraphQL types
if [ "$SKIP_CODEGEN" = false ]; then
    print_info "Generating GraphQL types..."
    cd web
    if pnpm codegen; then
        print_success "GraphQL types generated"
    else
        print_error "Failed to generate GraphQL types"
        cd ..
        if [ ! -z "$BACKEND_PID" ]; then
            kill $BACKEND_PID 2>/dev/null
        fi
        exit 1
    fi
    cd ..
else
    print_info "Skipping GraphQL codegen"
fi

# Step 5: Run type checking
print_info "Running type check..."
cd web
if pnpm typecheck; then
    print_success "Type check passed"
else
    print_warning "Type check failed - there may be type errors to fix"
fi
cd ..

# Step 6: Run linting
print_info "Running linter..."
cd web
if pnpm lint; then
    print_success "Linting passed"
else
    print_warning "Linting failed - run 'pnpm lint:fix' to auto-fix issues"
fi
cd ..

# Step 7: Start development server
print_info "Starting frontend development server..."
cd web

# Cleanup function
cleanup() {
    print_info "Cleaning up..."
    if [ ! -z "$BACKEND_PID" ]; then
        print_info "Stopping backend server..."
        kill $BACKEND_PID 2>/dev/null
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

if [ "$WATCH_MODE" = true ]; then
    print_info "Starting in watch mode..."
    print_info "Frontend: http://localhost:5173"
    print_info "Backend: http://localhost:8000"
    print_info "GraphQL: http://localhost:8000/graphql"
    print_info "Press Ctrl+C to stop"
    
    # Start codegen in watch mode in background
    pnpm codegen:watch > ../logs/codegen.log 2>&1 &
    CODEGEN_PID=$!
    
    # Start frontend dev server
    pnpm dev
    
    # Cleanup codegen watch
    if [ ! -z "$CODEGEN_PID" ]; then
        kill $CODEGEN_PID 2>/dev/null
    fi
else
    print_success "Frontend development environment is ready!"
    print_info "Run 'cd web && pnpm dev' to start the development server"
    print_info "Frontend will be available at: http://localhost:5173"
    print_info "Backend API is at: http://localhost:8000"
    print_info "GraphQL playground is at: http://localhost:8000/graphql"
fi

# Cleanup
cleanup