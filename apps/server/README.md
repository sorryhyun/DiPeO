# DiPeO Backend Server

FastAPI-based backend server implementing the unified execution engine for the DiPeO (Diagrammed People & Organizations) visual programming environment.

## Commands

### Development
```bash
# Run server with auto-reload
RELOAD=true python -m apps.server.main

# Run server without reload
python -m apps.server.main

# Run server on custom port
PORT=8001 python -m apps.server.main

# Install dependencies
pip install -r requirements.txt

# Validate installation
python run_tests.py validate
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_api_integration.py -v

# Run specific test marker
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Run only integration tests
pytest -m unit        # Run only unit tests
pytest -m performance # Run performance tests
pytest -m e2e        # Run end-to-end tests

# Run a single test
pytest tests/test_api_integration.py::test_api_key_management -v

# Using the test runner script
python run_tests.py unit         # Run unit tests only
python run_tests.py integration  # Run integration tests
python run_tests.py performance  # Run performance benchmarks
python run_tests.py e2e         # Run end-to-end tests
python run_tests.py all         # Run all test suites
python run_tests.py coverage    # Generate coverage report
python run_tests.py benchmark   # Run execution benchmarks
```

### Diagram Execution (CLI)
```bash
# Primary execution method - pre-loads models, opens browser, then runs
python ../../tool.py run-and-monitor diagram.json

# Other execution modes
python ../../tool.py run diagram.json                    # Backend execution with streaming
python ../../tool.py run --no-stream diagram.json        # Backend execution without streaming
python ../../tool.py run-headless diagram.json           # Pure backend execution
python ../../tool.py monitor                             # Open browser monitoring
```

## Architecture

DiPeO Server implements a **unified backend execution model** where all diagram nodes execute server-side through the V2 API (`/api/v2/run-diagram`). This provides consistent execution, centralized security, and SSE streaming for real-time updates.

### Core Components

**Execution Engine** (`src/engine/`)
- `engine.py`: UnifiedExecutionEngine orchestrates all diagram execution
- `executors/`: Node-specific executors (StartExecutor, JobExecutor, PersonJobExecutor, etc.)
- `planner.py`: Creates execution plans with dependency analysis
- `resolver.py`: Topological sorting and cycle detection
- `controllers.py`: Loop iteration and skip management

**Node Type Normalization**
- Frontend uses camelCase with "Node" suffix: `startNode`, `personJobNode`
- Backend uses snake_case without suffix: `start`, `person_job`
- `src/utils/node_type_utils.py` handles automatic conversion

**Service Layer** (`src/services/`)
- Uses AppContext dependency injection pattern
- No @lru_cache() singletons - proper lifecycle management
- Services initialized at startup via FastAPI lifespan context

### Loop Implementation

Loops use PersonJob nodes with `iterationCount` and Condition nodes:
- PersonJob executes **at most** N times based on `iterationCount` (can be fewer due to errors or other skip conditions)
- Execution count starts at 0; node skips when count >= max_iterations
- Condition node with `conditionType: "detect_max_iterations"` controls loop exit:
  - Returns `false` while ANY node with max_iterations hasn't reached its limit
  - Returns `true` when ALL nodes with max_iterations have reached their limits
  - Only checks nodes that have max_iterations defined (ignores others)

**Example**: Two PersonJob nodes with max_iterations=2:
- Iteration 1: Both execute (count 0→1), Condition returns `false` 
- Iteration 2: Both execute (count 1→2), Condition returns `false`
- Iteration 3: Both skip (count=2), Condition returns `true` → loop exits

### Variable Substitution
- Arrow labels become variable names (arrow labeled "topic" → `{{topic}}`)
- Backend `_substitute_variables()` replaces `{{var}}` patterns in prompts


Use pytest markers to run specific test categories during development.

## Common Development Tasks

### Adding a New Node Type
1. Define in `src/constants.py` NodeType enum
2. Create executor in `src/engine/executors/` inheriting from BaseExecutor
3. Implement `validate()` and `execute()` methods
4. Register in ExecutorFactory in `engine.py`

### Adding a New LLM Provider
1. Create adapter in `src/llm/adapters/` inheriting from BaseAdapter
2. Implement `chat()` method following the interface
3. Register in `src/llm/factory.py`
4. Add to SUPPORTED_MODELS in `src/llm/__init__.py`

### Debugging Execution Issues
1. Check node type normalization if frontend/backend mismatch
2. Verify arrow labels match variable names in prompts
3. Use debug mode for continue-on-error behavior
4. Monitor SSE stream events for execution flow

## API Documentation

Access interactive API documentation when server is running:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

```bash
# Server configuration
PORT=8000                           # Server port (default: 8000)
RELOAD=false                        # Auto-reload for development
BASE_DIR=/path/to/project          # Base directory for file operations

# Storage configuration
REDIS_URL=redis://localhost:6379    # Optional Redis for memory service
API_KEY_STORE_FILE=apikeys.json    # API key storage location

# LLM configuration (if not using API key service)
OPENAI_API_KEY=sk-...              # OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...       # Claude API key
GOOGLE_API_KEY=...                 # Gemini API key
XAI_API_KEY=...                    # Grok API key
```

## SSE Streaming Events

The V2 API streams execution progress via Server-Sent Events:

```javascript
// Execution lifecycle events
{type: 'execution_started', execution_id: '...', total_nodes: 5}
{type: 'node_start', nodeId: '...', nodeType: 'person_job'}
{type: 'node_progress', nodeId: '...', message: 'Processing...'}
{type: 'node_complete', nodeId: '...', output: {...}, cost: 0.02}
{type: 'node_skipped', nodeId: '...', reason: 'max_iterations_reached'}
{type: 'node_error', nodeId: '...', error: 'Connection timeout'}
{type: 'execution_complete', total_cost: 0.05, duration: 3.2}
{type: 'execution_error', error: 'No start nodes found'}
```

## Error Handling Patterns

Use the centralized error handling decorator for API endpoints:

```python
from src.api.middleware import handle_api_errors

@router.post("/your-endpoint")
@handle_api_errors
async def your_endpoint(request: Request):
    # Automatic error formatting and logging
    pass
```

Custom exceptions hierarchy:
- `DiagramExecutionError`: Base for all execution errors
- `ValidationError`: Input validation failures
- `LLMServiceError`: LLM provider errors
- `FileOperationError`: File access issues
- `APIKeyNotFoundError`: Missing API keys
- `NodeExecutionError`: Node-specific failures