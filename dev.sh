#!/bin/bash

# DiPeO Development Script
# This script handles CLI setup, code generation, and running frontend/backend services

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Default values
INSTALL_CLI=false
GENERATE_CODE=false
RUN_FRONTEND=false
RUN_BACKEND=false
RUN_ALL=false
WATCH_MODE=false

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command_exists "node"; then
        missing_deps+=("node")
    fi
    
    if ! command_exists "pnpm"; then
        missing_deps+=("pnpm")
    fi
    
    if ! command_exists "python3"; then
        missing_deps+=("python3")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_info "Please install the missing dependencies and try again."
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

# Function to install/setup CLI
install_cli() {
    print_info "Setting up DiPeO CLI..."
    
    cd "$SCRIPT_DIR/cli"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install CLI in development mode
    print_info "Installing CLI in development mode..."
    pip install -e .
    
    print_success "CLI installed successfully"
    print_info "You can now use 'dipeo' command (in the virtual environment)"
    
    cd "$SCRIPT_DIR"
}

# Function to generate code
generate_code() {
    print_info "Running code generation..."
    
    # Build domain models and generate all code
    cd "$SCRIPT_DIR/packages/domain-models"
    
    print_info "Building TypeScript models..."
    pnpm build
    
    print_success "Code generation completed"
    
    cd "$SCRIPT_DIR"
}

# Function to run backend
run_backend() {
    print_info "Starting backend server..."
    
    cd "$SCRIPT_DIR/server"
    
    # Check if virtual environment exists
    if [ ! -d "../server/.venv" ]; then
        print_warning "Backend virtual environment not found. Creating one..."
        python3 -m venv ../.venv
        source ../.venv/bin/activate
        pip install -r requirements.txt
    else
        source ../.venv/bin/activate
    fi
    
    # Run the backend
    print_info "Starting FastAPI server on http://localhost:8000"
    python main.py
}

# Function to run frontend
run_frontend() {
    print_info "Starting frontend development server..."
    
    cd "$SCRIPT_DIR"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_info "Installing frontend dependencies..."
        pnpm install
    fi
    
    # Run frontend with or without watch mode
    if [ "$WATCH_MODE" = true ]; then
        print_info "Starting frontend in watch mode..."
        pnpm dev
    else
        print_info "Starting frontend..."
        pnpm dev
    fi
}

# Function to run both frontend and backend
run_all() {
    print_info "Starting both frontend and backend..."
    
    # Check if tmux is available
    if command_exists "tmux"; then
        print_info "Using tmux to run services in parallel..."
        
        # Kill existing tmux session if it exists
        tmux kill-session -t dipeo 2>/dev/null || true
        
        # Create new tmux session
        tmux new-session -d -s dipeo -n backend
        tmux send-keys -t dipeo:backend "$SCRIPT_DIR/dev.sh --backend" C-m
        
        tmux new-window -t dipeo -n frontend
        tmux send-keys -t dipeo:frontend "$SCRIPT_DIR/dev.sh --frontend" C-m
        
        print_success "Services started in tmux session 'dipeo'"
        print_info "Use 'tmux attach -t dipeo' to view the services"
        print_info "Use 'tmux kill-session -t dipeo' to stop all services"
    else
        print_warning "tmux not found. Running services sequentially..."
        print_info "Install tmux for better parallel execution"
        print_info "Starting backend in background..."
        
        # Run backend in background
        run_backend &
        BACKEND_PID=$!
        
        # Wait a bit for backend to start
        sleep 5
        
        # Run frontend (this will block)
        run_frontend
        
        # Kill backend when frontend exits
        kill $BACKEND_PID 2>/dev/null || true
    fi
}

# Function to show usage
show_usage() {
    cat << EOF
DiPeO Development Script

Usage: $0 [OPTIONS]

Options:
    --help, -h          Show this help message
    --install-cli       Install/setup the CLI tool
    --generate, -g      Run code generation
    --frontend, -f      Run frontend development server
    --backend, -b       Run backend server
    --all, -a           Run both frontend and backend
    --watch, -w         Run in watch mode (with --all or --frontend)
    
Examples:
    # Install CLI and generate code
    $0 --install-cli --generate
    
    # Run both frontend and backend
    $0 --all
    
    # Run frontend in watch mode
    $0 --frontend --watch
    
    # Do everything: install CLI, generate code, and run all services
    $0 --install-cli --generate --all

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            exit 0
            ;;
        --install-cli)
            INSTALL_CLI=true
            shift
            ;;
        --generate|-g)
            GENERATE_CODE=true
            shift
            ;;
        --frontend|-f)
            RUN_FRONTEND=true
            shift
            ;;
        --backend|-b)
            RUN_BACKEND=true
            shift
            ;;
        --all|-a)
            RUN_ALL=true
            shift
            ;;
        --watch|-w)
            WATCH_MODE=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# If no options provided, show usage
if [ "$INSTALL_CLI" = false ] && [ "$GENERATE_CODE" = false ] && [ "$RUN_FRONTEND" = false ] && [ "$RUN_BACKEND" = false ] && [ "$RUN_ALL" = false ]; then
    show_usage
    exit 0
fi

# Main execution
print_info "DiPeO Development Script"
print_info "========================"

# Check dependencies
check_dependencies

# Execute requested actions
if [ "$INSTALL_CLI" = true ]; then
    install_cli
fi

if [ "$GENERATE_CODE" = true ]; then
    generate_code
fi

if [ "$RUN_ALL" = true ]; then
    run_all
elif [ "$RUN_BACKEND" = true ]; then
    run_backend
elif [ "$RUN_FRONTEND" = true ]; then
    run_frontend
fi

print_success "Done!"