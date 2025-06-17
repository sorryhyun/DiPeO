# DiPeO Development Scripts

## Frontend Development Script

The `frontend-dev.sh` script automates the frontend development workflow for DiPeO.

### Usage

```bash
# Basic usage - starts everything
./scripts/frontend-dev.sh

# Watch mode - keeps running with auto-reload
./scripts/frontend-dev.sh --watch

# Skip certain steps
./scripts/frontend-dev.sh --skip-install    # Skip pnpm install
./scripts/frontend-dev.sh --skip-server     # Skip backend server startup
./scripts/frontend-dev.sh --skip-codegen    # Skip GraphQL codegen

# Combine options
./scripts/frontend-dev.sh --skip-install --watch
```

### What it does

1. **Installs dependencies** - Runs `pnpm install` to ensure all packages are up to date
2. **Starts backend server** - Launches the FastAPI server if not already running
3. **Downloads GraphQL schema** - Fetches the latest schema from the backend
4. **Generates TypeScript types** - Runs GraphQL codegen to create type definitions
5. **Runs type checking** - Validates TypeScript types with `pnpm typecheck`
6. **Runs linting** - Checks code style with `pnpm lint`
7. **Starts dev server** - In watch mode, starts the Vite development server

### Prerequisites

- Node.js and pnpm installed
- Python environment set up for the backend
- Backend dependencies installed (`cd server && pip install -r requirements.txt`)

### Logs

The script creates log files in the `logs/` directory:
- `backend.log` - Backend server output
- `codegen.log` - GraphQL codegen output (in watch mode)

### Ports

- Frontend dev server: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- GraphQL playground: `http://localhost:8000/graphql`

### Troubleshooting

If the script fails:

1. **Port already in use**: The script checks if port 8000 is already in use. If you have another service on this port, stop it first.

2. **Backend fails to start**: Check `logs/backend.log` for error messages. Common issues:
   - Missing Python dependencies
   - Database connection issues
   - Port conflicts

3. **GraphQL codegen fails**: This usually means:
   - Backend server isn't running
   - Schema has breaking changes
   - Network connectivity issues

4. **Type checking fails**: This is expected if there are TypeScript errors in the codebase. Fix the errors and re-run.

### Development Workflow

1. Run the script in watch mode: `./scripts/frontend-dev.sh --watch`
2. Make changes to your code
3. The frontend will auto-reload
4. GraphQL types will regenerate automatically when schema changes
5. Press Ctrl+C to stop everything

### CI/CD Integration

For CI environments, use:

```bash
# Download schema only (requires backend to be running)
cd web && pnpm download-schema

# Generate types without starting servers
cd web && pnpm codegen

# Run all checks
cd web && pnpm typecheck && pnpm lint
```