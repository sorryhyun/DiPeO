# DiPeO Quick Commands



```bash
# Start backend (single worker for WebSocket compatibility)
./run-server.sh
# code generation + run front-end
./front.sh
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