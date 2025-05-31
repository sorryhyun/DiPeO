# AgentDiagram Server

A FastAPI-based backend server for executing visual agent diagrams with LLM integrations, streaming capabilities, and conversation memory management.

## Overview

AgentDiagram Server executes flow-based diagrams where nodes represent different operations (LLM calls, conditions, data sources) connected by arrows defining execution flow. It supports real-time streaming updates, conversation memory, and multiple LLM providers.

## Architecture

```
apps/server/
├── src/
│   ├── api/           # REST API endpoints
│   ├── execution/     # V2 execution engine
│   ├── llm/           # LLM adapters (OpenAI, Anthropic, etc.)
│   ├── services/      # Business logic services
│   ├── streaming/     # SSE streaming support
│   └── utils/         # Shared utilities
├── tests/             # Test suite
├── config.py          # Configuration management
└── main.py            # Application entry point
```

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the Server

```bash
# Development mode with auto-reload
python -m apps.server.main

# Production mode
uvicorn apps.server.main:app --host 0.0.0.0 --port 8000
```

## Core Features

### Node Types

- **StartNode**: Entry point for diagram execution
- **PersonJobNode**: LLM agent interactions with memory
- **PersonBatchJobNode**: Batch processing with LLM agents
- **ConditionNode**: Boolean branching logic
- **DBNode**: Data source operations (files, code, fixed prompts)
- **JobNode**: Stateless operations (API calls, code execution)
- **EndpointNode**: Terminal nodes with optional file saving

### Supported LLM Providers

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3.5, Claude 3)
- Google (Gemini 2.0, Gemini 1.5)
- xAI (Grok 2)

### API Endpoints

#### Diagram Execution
```
POST /api/run-diagram         # Execute with SSE streaming
POST /api/run-diagram-sync    # Synchronous execution
POST /api/stream/run-diagram  # Alias for streaming
```

#### Diagram Management
```
POST /api/import-uml          # Import UML format
POST /api/import-yaml         # Import YAML format
POST /api/export-uml          # Export to UML
POST /api/save                # Save diagram
```

#### API Keys
```
GET  /api/api-keys            # List stored keys
POST /api/api-keys            # Add new key
DELETE /api/api-keys/{id}     # Remove key
GET  /api/models              # List available models
```

#### Files
```
POST /api/upload-file         # Upload file
```

#### Conversations
```
GET  /api/conversations       # Get conversation history
POST /api/conversations/clear # Clear all conversations
```

#### Monitoring
```
GET  /api/monitor/stream      # SSE endpoint for all executions
GET  /api/health              # Health check
GET  /metrics                 # Prometheus metrics
```

## Development

### Project Structure

**Execution Engine (V2)**
- `execution/core/`: Core execution components
- `execution/executors/`: Node-specific executors
- `execution/flow/`: Dependency resolution and planning
- `execution/memory/`: Conversation memory management

**Services**
- `DiagramService`: Diagram operations and validation
- `LLMService`: Unified LLM provider interface
- `MemoryService`: Conversation persistence (Redis/in-memory)
- `UnifiedFileService`: Secure file operations
- `APIKeyService`: API key management

### Adding New Features

#### New Node Type
1. Create executor in `src/execution/executors/`
2. Register in `ExecutionEngine._create_executors()`
3. Add to `NodeType` enum in `constants.py`

#### New LLM Provider
1. Create adapter in `src/llm/adapters/`
2. Update factory in `src/llm/factory.py`
3. Add to `SUPPORTED_MODELS` mapping

### Error Handling

Unified error system with custom exceptions:
- `ValidationError`: Input validation failures
- `DiagramExecutionError`: Execution failures
- `NodeExecutionError`: Node-specific errors
- `LLMServiceError`: LLM call failures

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps.server

# Run specific test file
pytest apps/server/tests/test_diagram_service.py
```

## Configuration

### Environment Variables
```env
BASE_DIR=/path/to/project      # Base directory for file operations
REDIS_URL=redis://localhost    # Redis for distributed memory (optional)
API_KEY_STORE_FILE=apikeys.json # API key storage location
PORT=8000                      # Server port
RELOAD=false                   # Auto-reload for development
```

### File Storage
- Uploads: `{BASE_DIR}/uploads/`
- Results: `{BASE_DIR}/results/`
- Logs: `{BASE_DIR}/conversation_logs/`

## Streaming Architecture

The server supports Server-Sent Events (SSE) for real-time execution updates:

1. **Execution Updates**: Node status changes during execution
2. **Monitor Stream**: Global stream for all diagram executions
3. **Heartbeat**: Automatic keep-alive for long-running executions

## Memory Management

Conversation memory supports:
- Per-person conversation history
- Execution-scoped memory isolation
- Redis backend for distributed deployments
- Automatic conversation log persistence

## Security Considerations

- Path traversal protection in file operations
- API key encryption (stored as plain text - use environment variables in production)
- Input validation on all endpoints
- CORS configured for development (restrict in production)

## Performance

- Connection pooling for LLM adapters
- Async/await throughout for concurrent operations
- Redis caching for conversation history
- Streaming responses to reduce memory usage

## Troubleshooting

### Common Issues

1. **"No start nodes found"**: Ensure diagram has at least one `startNode`
2. **API key errors**: Verify keys are properly configured in UI
3. **Memory errors**: Check Redis connection or fallback to in-memory
4. **File permissions**: Ensure write access to BASE_DIR subdirectories

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Follow existing code structure and patterns
2. Add tests for new features
3. Update this README for significant changes
4. Use type hints and docstrings
5. Handle errors gracefully with proper exceptions