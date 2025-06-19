# DiPeO Development Scripts

This document describes the various scripts available for development and operations.

## Quick Start

```bash
# Start everything (frontend + backend)
./run.sh

# Or use the development script
./dev.sh --all
```

## Available Scripts

### 1. `run.sh` - Quick Start Script
The simplest way to start DiPeO. Handles first-time setup automatically.

```bash
# Start both frontend and backend (default)
./run.sh
./run.sh all

# Start only frontend
./run.sh frontend
./run.sh f

# Start only backend  
./run.sh backend
./run.sh b
```

### 2. `dev.sh` - Development Script
Comprehensive development script with multiple options.

```bash
# Show help
./dev.sh --help

# Install CLI tool
./dev.sh --install-cli

# Run code generation
./dev.sh --generate

# Start frontend
./dev.sh --frontend
./dev.sh --frontend --watch  # with watch mode

# Start backend
./dev.sh --backend

# Start both frontend and backend
./dev.sh --all

# Do everything (install, generate, run)
./dev.sh --install-cli --generate --all
```

### 3. `codegen.sh` - GraphQL Code Generation
Exports GraphQL schema from backend and generates TypeScript types.

```bash
# Generate GraphQL types
./codegen.sh

# Generate and start frontend
./codegen.sh --dev
```

### 4. `dipeo` - CLI Wrapper
Convenient wrapper for the DiPeO CLI tool.

```bash
# Run a diagram
./dipeo run files/diagrams/example.yaml --debug

# List available commands
./dipeo --help

# Show version
./dipeo version
```

### 5. `frontend-dev.sh` - Frontend Development Helper
Specialized script for frontend development with additional options.

```bash
# Basic frontend start
./frontend-dev.sh

# With watch mode for code generation
./frontend-dev.sh --watch
```

## First Time Setup

When you clone the repository for the first time:

```bash
# Option 1: Use the quick start (recommended)
./run.sh

# Option 2: Manual setup
pnpm install                    # Install dependencies
./dev.sh --generate            # Generate code
./dev.sh --install-cli         # Install CLI (optional)
./dev.sh --all                 # Start services
```

## Development Workflow

### Full Stack Development
```bash
# Terminal 1: Start everything
./run.sh

# Terminal 2: Make changes and regenerate if needed
./dev.sh --generate
```

### Frontend Only Development
```bash
# Start frontend with hot reload
./dev.sh --frontend --watch
```

### Backend Only Development
```bash
# Start backend
./dev.sh --backend
```

### Working with Diagrams
```bash
# Run a diagram
./dipeo run files/diagrams/my-diagram.yaml --debug --timeout=10

# Monitor execution
./dipeo run files/diagrams/my-diagram.yaml --monitor
```

### Code Generation
```bash
# Generate all code (Python, GraphQL, CLI models)
./dev.sh --generate

# Generate only GraphQL types for frontend
./codegen.sh
```

## Script Features

- **Automatic dependency checking**: Scripts verify required tools are installed
- **First-time setup detection**: Automatically installs dependencies when needed
- **Color-coded output**: Clear visual feedback for different message types
- **Error handling**: Scripts exit cleanly on errors with helpful messages
- **Virtual environment management**: Python scripts handle venv creation/activation
- **Parallel execution support**: Uses tmux when available for running multiple services

## Requirements

- Node.js (with pnpm)
- Python 3.8+
- tmux (optional, for parallel service execution)

## Troubleshooting

### Services not starting
```bash
# Check dependencies
./dev.sh --help  # Will check and report missing dependencies

# Clean install
rm -rf node_modules pnpm-lock.yaml
pnpm install
./dev.sh --generate
```

### Port already in use
```bash
# Frontend (port 5173)
lsof -ti:5173 | xargs kill -9

# Backend (port 8000)
lsof -ti:8000 | xargs kill -9
```

### CLI not working
```bash
# Reinstall CLI
rm -rf apps/cli/.venv
./dev.sh --install-cli
```

## Tips

1. Use `tmux` for better parallel execution of services
2. The `run.sh` script is best for quick starts
3. Use `dev.sh` for more control over individual components
4. Keep the GraphQL schema in sync with `./codegen.sh` after backend changes
5. Use `./dipeo` instead of `python tool.py` for running diagrams