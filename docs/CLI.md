# DiPeO CLI Development Guide

## Architecture Overview
The DiPeO CLI is a GraphQL-based command-line tool for executing flow diagrams. It follows a modular design with separate command implementations and async execution handling.

```
cli/
├── __main__.py      # Entry point
├── api_client.py    # GraphQL client with subscriptions
├── run.py           # Diagram execution command
├── monitor.py       # Browser monitoring
├── convert.py       # Format conversion (JSON/YAML)
├── stats.py         # Diagram statistics
├── models.py        # Local validation models
└── utils.py         # Shared utilities
```

## Core Components

### 1. API Client (`api_client.py`)
- Uses `gql` library for GraphQL operations
- Separate transports: HTTP for queries/mutations, WebSocket for subscriptions
- Key methods: `execute_diagram()`, `subscribe_to_execution()`, `subscribe_to_node_updates()`

### 2. Command Structure
Each command is a standalone module with a `<command>_command()` function:
```python
async def run_command(args: List[str]) -> None:
    # Parse options
    options = _parse_run_options(args[1:])
    # Load diagram
    diagram = DiagramLoader.load(args[0])
    # Execute via GraphQL
    executor = DiagramExecutor(options)
    result = await executor.execute(diagram)
```

### 3. Execution Flow
1. Load diagram from file (JSON/YAML)
2. Validate using local models
3. Save diagram to server via GraphQL
4. Start execution and get execution ID
5. Subscribe to real-time updates (parallel streams)
6. Handle interactive prompts if needed
7. Save results

## Key Features

### Real-time Streaming
Three concurrent subscription streams during execution:
- **Node updates**: Progress and output for each node
- **Execution updates**: Overall execution status
- **Interactive prompts**: User input requests

### Error Handling
- Timeout mechanism (default 300s)
- Graceful cancellation of async tasks
- Debug mode for detailed output

## Development Workflow

### Adding a New Command
1. Create `cli/<command>.py`
2. Implement `<command>_command(args: List[str])`
3. Add to `cli/__init__.py` exports
4. Register in `__main__.py` command dispatcher

### Testing
```bash
# Run test script
python cli/test_cli.py

# Test individual commands
python -m cli run test_diagram.yaml --debug
python -m cli stats test_diagram.json
```

### GraphQL Schema Updates
When server schema changes:
1. Update query/mutation/subscription strings in `api_client.py`
2. Adjust response parsing logic
3. Update local models if needed

## Best Practices
- Keep commands focused and independent
- Use async/await for all I/O operations
- Validate diagrams locally before sending to server
- Handle subscription streams concurrently
- Provide clear user feedback during execution
- Always clean up resources (close transports)

## Dependencies
- `gql[all]`: GraphQL client with subscription support
- `pyyaml`: YAML file handling
- `aiohttp`: Async HTTP transport
- `websockets`: WebSocket transport for subscriptions