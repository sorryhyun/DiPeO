# DiPeO Quick Commands

## Common Tasks

### =� Development Server
```bash
# Start backend (single worker for WebSocket compatibility)
./run-server.sh

# Start frontend (React dev server)
pnpm dev:web
```

### =� GraphQL Schema
```bash
# Export GraphQL schema to frontend
./export-schema.sh
# Output: apps/web/src/graphql/schema.graphql
```

### <� Run Diagrams
```bash
# Basic run
python tool.py run files/diagrams/diagram.json

# With monitoring
python tool.py run files/diagrams/diagram.json --monitor

# Debug mode (10s timeout)
python tool.py run files/diagrams/diagram.json --debug --timeout=10
```

### =' Code Quality
```bash
# Lint & fix
pnpm lint:fix

# Type check
pnpm typecheck

# Build frontend
pnpm build:web
```

### =� Quick Notes
- Always use `pnpm` (not npm/npx)
- Backend requires `WORKERS=1` for WebSocket development
- Default OpenAI model: `gpt-4.1-nano`
- Test API key: `APIKEY_387B73`