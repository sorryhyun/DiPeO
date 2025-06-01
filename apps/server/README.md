# AgentDiagram Server

FastAPI backend for executing visual agent diagrams with LLM integrations and streaming support.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python -m apps.server.main

# Or with auto-reload
RELOAD=true python -m apps.server.main
```

Server runs at `http://localhost:8000`

## Architecture

```
src/
├── api/          # REST endpoints & middleware
├── llm/          # LLM adapters (OpenAI, Claude, Gemini, Grok)
├── services/     # Business logic
├── utils/        # Shared utilities
├── constants.py  # Enums and configuration
└── exceptions.py # Custom exception types
```

### Key Services

- **DiagramService**: Diagram validation and import/export
- **LLMService**: Unified LLM interface with connection pooling
- **MemoryService**: Conversation memory (Redis/in-memory)
- **UnifiedFileService**: Secure file operations
- **APIKeyService**: API key management

## Node Types

| Node | Purpose | Key Features |
|------|---------|--------------|
| `startNode` | Entry point | Initial context/input |
| `personJobNode` | LLM agent | Stateful conversations with memory |
| `conditionNode` | Branching | Boolean expressions |
| `dbNode` | Data source | Files, code execution, fixed prompts |
| `endpointNode` | Output | Save results to files |

## API Endpoints

### Execution
- `POST /api/run-diagram` - Execute with SSE streaming
- `POST /api/stream/run-diagram` - Alias for streaming
- `GET /api/monitor/stream` - Monitor all executions

### Management
- `GET/POST/DELETE /api/api-keys` - API key CRUD
- `POST /api/upload-file` - File upload
- `POST /api/import-uml` - Import PlantUML
- `POST /api/export-uml` - Export to PlantUML

### Conversations
- `GET /api/conversations` - Query history with filtering
- `POST /api/conversations/clear` - Clear memory

## Development

### Adding a New LLM Provider

1. Create adapter in `src/llm/adapters/`:
```python
class YourAdapter(BaseAdapter):
    def chat(self, system_prompt: str, user_prompt: str, **kwargs) -> ChatResult:
        # Implementation
        pass
```

2. Register in `src/llm/factory.py`:
```python
if provider == 'your_provider':
    return YourAdapter(model_name, api_key)
```

3. Add to `SUPPORTED_MODELS` in `src/llm/__init__.py`

### Adding a New Node Type

1. Define in `src/constants.py`:
```python
class NodeType(Enum):
    YOUR_NODE = "yourNode"
```

2. Create executor (if using V2 engine) or add logic to execution flow

### Error Handling

```python
from src.core import handle_api_errors

@router.post("/endpoint")
@handle_api_errors
async def your_endpoint():
    # Automatic error formatting
    pass
```

Custom exceptions in `src/exceptions.py`:
- `ValidationError` - Input validation
- `DiagramExecutionError` - Execution failures
- `LLMServiceError` - LLM call failures
- `FileOperationError` - File access issues

## Configuration

Environment variables:
```env
PORT=8000                       # Server port
RELOAD=false                    # Auto-reload
BASE_DIR=/path/to/project       # Base for file ops
REDIS_URL=redis://localhost     # Optional Redis
API_KEY_STORE_FILE=apikeys.json # API key storage
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=apps.server

# Specific module
pytest apps/server/tests/test_services.py -v
```

Test fixtures in `tests/fixtures/`:
- `mocks.py` - Service mocks
- `diagrams.py` - Sample diagram structures

## Streaming Response Format

SSE events during execution:
```javascript
{type: 'execution_started', execution_id: '...'}
{type: 'node_start', nodeId: '...'}
{type: 'node_complete', nodeId: '...', output_preview: '...'}
{type: 'execution_complete', context: {...}, total_cost: 0.05}
{type: 'execution_error', error: '...'}
```

## Common Issues

1. **No start nodes**: Diagram must have `startNode`
2. **API key not found**: Check key exists in UI/storage
3. **LLM timeout**: Retry logic handles transient failures
4. **File not found**: Check `BASE_DIR` and relative paths

## CLI Tool

```bash
# Run diagram
python agentdiagram_tool.py run diagram.json

# Monitor executions
python agentdiagram_tool.py monitor

# Convert formats
python agentdiagram_tool.py convert input.puml output.json
```

## Security Notes

- Path traversal protection via `validate_file_path()`
- API keys stored plaintext (use env vars in production)
- CORS enabled for development (restrict for production)
- File uploads restricted to `UPLOAD_DIR`