# Infrastructure Layer Architecture

Concrete implementations of domain ports for all I/O operations, following the ports and adapters (hexagonal) architecture pattern.

## Architectural Patterns

### Port/Adapter Pattern
Domain defines interfaces (ports), infrastructure implements them (adapters):

```python
# Port (defined in domain)
class BlobStorePort(Protocol):
    async def put(self, key: str, data: bytes) -> str:
        ...

# Adapter (implemented in infrastructure)
from dipeo.infrastructure.storage.local import LocalBlobAdapter

class LocalBlobAdapter(BlobStorePort):
    async def put(self, key: str, data: bytes) -> str:
        pass
```

### Driver Pattern
Orchestrates multiple adapters with mixin composition:

```python
class DiagramService(LoggingMixin, ValidationMixin, DiagramPort):
    def __init__(self, storage: DiagramStoragePort, converter: DiagramConverterService):
        pass
```

### Configuration Pattern
Centralized settings:

```python
from dipeo.infrastructure.config import get_settings
settings = get_settings()  # Uses DIPEO_* env vars
```

## Module Structure

| Module | Purpose |
|--------|---------|
| `codegen/` | TypeScript AST parsing, Jinja2 templates |
| `diagram/` | Diagram compilation, storage, conversion, prompt templates |
| `events/` | Event bus (in-memory, Redis) |
| `execution/` | State management, message routing |
| `integrations/` | External APIs (Notion, Slack) |
| `llm/` | LLM providers (unified clients), domain adapters, simplified service |
| `common/` | Shared utilities (cache, locks) |
| `security/` | API key management and security services |
| `storage/` | All storage concerns (filesystem, blob, artifacts, conversation, JSON DB) |
| `database/` | [DEPRECATED] Moved to `storage/json_db/` - backward compatibility only |

## Key Components

### Storage Adapters (`storage/`)

Organized by storage type:

| Adapter | Location | Use Case |
|---------|----------|----------|
| `LocalFileSystemAdapter` | `storage/local/` | Config files, temp files |
| `LocalBlobAdapter` | `storage/local/` | Versioned storage |
| `S3Adapter` | `storage/cloud/` | Cloud deployments |
| `ArtifactStoreAdapter` | `storage/artifacts/` | ML models, binaries |
| `InMemoryConversationRepository` | `storage/conversation/` | Fast, ephemeral conversation storage |
| `InMemoryPersonRepository` | `storage/conversation/` | Person entity management |

### Diagram Infrastructure (`diagram/`)

- **adapters/**: Diagram-specific adapters for various formats
- **drivers/**: High-level diagram services and orchestration
- **prompt_templates/**: Prompt template processing
  - `PromptBuilder`: Builds prompts from templates with variable substitution and caching
    - Template caching with 1000 entry limit
    - Cache key based on template + values for deduplication
    - Automatic cleanup when cache exceeds limit
  - `SimpleTemplateProcessor`: Template processing implementation using Jinja2

### JSON Database Services (`storage/json_db/`)

- **DBOperationsDomainService**: JSON file-based database operations
- **Location**: Moved from `database/` to `storage/json_db/`
- **Features**: File-based storage with database-like operations (read/write/append/update)
- **Note**: Backward compatibility maintained via `database/__init__.py`

### Security Services (`security/`)

- **APIKeyService**: Core API key management interface
- **EnvironmentAPIKeyService**: Environment-based API key provider
- **Location**: Moved from `shared/keys/` to `security/keys/`
- **Features**: Secure API key storage and retrieval

### Common Utilities (`common/`)

- **SingleFlightCache**: Prevents duplicate concurrent operations (`common/utils/cache.py`)
- **FileLock, AsyncFileLock, CacheFileLock**: File-based locking mechanisms (`common/utils/locks.py`)
- **Location**: Moved from `shared/drivers/utils/` to `common/utils/`
- **Features**: Thread-safe caching and file locking primitives

### LLM Infrastructure

**Unified Client Architecture**:
- Core types in `llm/core/types.py` (AdapterConfig, TokenUsage, LLMResponse)
- All providers use unified clients directly (no adapter/client separation)
- Each provider has a single `unified_client.py` file

**Provider Unified Clients** (`llm/providers/`):
- **OpenAI** (`UnifiedOpenAIClient`): Uses new `responses.create()` and `responses.parse()` APIs
  - `input` parameter instead of `messages`
  - `max_output_tokens` instead of `max_tokens`
  - `text_format` for structured output with Pydantic models
  - Temperature not supported in new API
- **Anthropic** (`UnifiedAnthropicClient`): Claude models with tool use support
- **Google** (`UnifiedGoogleClient`): Gemini models
- **Ollama** (`UnifiedOllamaClient`): Local model support with auto-pull
- **Claude Code** (`UnifiedClaudeCodeClient`): Claude Code SDK integration with session pooling

**Capabilities**:
- Retry logic with exponential backoff
- Streaming support (SSE mode)
- Structured output (JSON schema and Pydantic)
- Tool/function calling
- Phase-aware execution
- Batch processing support (provider-specific)

### Messaging

- **MessageRouter**: Central event distribution
- **Flow**: Engine → EventBus → MessageRouter → GraphQL/SSE
- **Unified EventBus**: Single protocol for all event handling

### Code Generation

- **parsers/**: TypeScript AST parsing
- **templates/**: Jinja2 with custom filters

## Environment Variables

```bash
DIPEO_BASE_DIR=/path/to/project    # Project root
DIPEO_PORT=8000                    # Server port
DIPEO_DEFAULT_LLM_MODEL=gpt-5-nano-2025-08-07  # Default LLM
DIPEO_LLM_TIMEOUT=300               # LLM timeout (seconds)
DIPEO_EXECUTION_TIMEOUT=3600       # Max execution time
DIPEO_PARALLEL_EXECUTION=true      # Enable parallel
```

## Component Lifecycle

```python
# 1. Create via DI container with mixin composition
service = DiagramService(storage, converter)  # Inherits LoggingMixin, ValidationMixin
# 2. Initialize (mixin methods available)
await service.initialize()
# 3. Use with mixin capabilities
diagram = await service.load_from_file("diagram.json")  # Auto-logging, validation
# 4. Cleanup
await service.cleanup()
```

## Error Handling Pattern

```python
try:
    result = await adapter.operation()
except Exception as e:
    raise StorageError(f"Operation failed: {e}")
```

## OpenAI API v2 Migration

DiPeO uses the new OpenAI API v2 patterns for LLM interactions:

### Key Changes from v1
- **Response Creation**: `responses.create()` instead of `chat.completions.create()`
- **Response Parsing**: `responses.parse()` for structured output
- **Input Parameter**: `input` instead of `messages`
- **Token Limits**: `max_output_tokens` instead of `max_tokens`
- **Structured Output**: `text_format` parameter with Pydantic models
- **Temperature**: Not supported in v2 API

### Example Usage
```python
from openai import OpenAI

client = OpenAI(api_key=api_key)

# Create response
response = client.responses.create(
    model="gpt-5-nano-2025-08-07",
    input="Your prompt here",
    max_output_tokens=1000
)

# Parse structured output
response = client.responses.parse(
    model="gpt-5-nano-2025-08-07",
    input="Your prompt here",
    text_format=YourPydanticModel
)

# Access response text
text = response.output[0].content[0].text
```

## Service Mixin Usage

DiPeO services use optional mixins for cross-cutting concerns. Mixins provide reusable functionality without monolithic inheritance:

### Available Mixins
- **LoggingMixin**: Structured logging with decorators
- **ValidationMixin**: Field and type validation
- **ConfigurationMixin**: Configuration management
- **CachingMixin**: In-memory caching with TTL
- **InitializationMixin**: Initialization tracking

### Using Mixins in Custom Services
```python
from dipeo.application.mixins import LoggingMixin, ValidationMixin, CachingMixin

class CustomService(LoggingMixin, ValidationMixin, CachingMixin):
    """Service with logging, validation, and caching capabilities."""

    def __init__(self, config: dict):
        # Initialize mixins
        LoggingMixin.__init__(self)
        ValidationMixin.__init__(self)
        CachingMixin.__init__(self, ttl=300)

        self.config = config

    async def process_data(self, data: dict) -> dict:
        # Use logging from LoggingMixin
        self.log_info("Processing data", extra={"data_size": len(data)})

        # Use validation from ValidationMixin
        if not self.validate_field(data, "required_field", str):
            raise ValueError("Invalid data")

        # Use caching from CachingMixin
        cache_key = f"processed_{data['id']}"
        if cached := self.get_cached(cache_key):
            return cached

        result = await self._do_processing(data)
        self.set_cached(cache_key, result)
        return result
```

### Mixin Composition Best Practices
1. **Order Matters**: List mixins left-to-right based on method resolution order
2. **Initialize Explicitly**: Call each mixin's `__init__()` in your service's `__init__()`
3. **Avoid Conflicts**: Don't mix multiple mixins with the same method names
4. **Use Selectively**: Only include mixins you actually need
5. **Document Usage**: Note which mixins a service uses in docstrings

## Best Practices

1. **Use Ports**: Import from `dipeo.domain.ports`, not concrete adapters
2. **Handle Retries**: Implement exponential backoff in adapters
3. **Async I/O**: All I/O operations should be async
4. **Centralize Config**: Use `get_settings()` for all configuration
5. **Log Operations**: Debug-level for normal ops, error for failures
6. **Compose with Mixins**: Use mixins for cross-cutting concerns instead of inheritance

## Adding New Infrastructure

### Storage Adapter
1. Implement port: `class RedisAdapter(BlobStorePort)` in appropriate `storage/` subdirectory
   - Local storage: `storage/local/`
   - Cloud storage: `storage/cloud/`
   - Artifact storage: `storage/artifacts/`
2. Register in DI container
3. Wire to services

### JSON Database Service
1. Implement JSON-based storage operations in `storage/json_db/`
2. Extend DBOperationsDomainService if needed
3. Register in DI container with FileSystemPort dependency

### Security Service
1. Create security service in `security/` (API keys, authentication, etc.)
2. Follow APIKeyService pattern for key management
3. Register in DI container with proper environment variable mapping

### Common Utility
1. Add utility to `common/utils/` (cache, locks, helpers)
2. Follow existing patterns (cache.py for caching, locks.py for locking)
3. Export from `common/__init__.py`

### LLM-based Adapter
1. Create adapter in `llm/adapters/`: `class CustomLLMAdapter`
2. Use orchestrator for person/facet management
3. Wire to appropriate handlers or evaluators

### Conversation Storage
1. Implement repository interface in `storage/conversation/`
2. Create adapter: `class RedisConversationRepository`
3. Register in DI container

### LLM Provider
1. Create unified client: `class UnifiedMistralClient` in `providers/mistral/unified_client.py`
2. Implement required methods: `async_chat()`, `stream()`, `batch_chat()`
3. Update factory in `llm/drivers/factory.py` to return the unified client
4. Export from `providers/mistral/__init__.py`

### External API
1. Create provider: `class JiraProvider(BaseProvider)`
2. Register in integrated API service

## Performance & Security

### Performance
- **Connection Pooling**: LLM adapters cache for 1 hour
- **Async I/O**: Use `asyncio.gather()` for parallel ops
- **Bounded Queues**: SSE uses `Queue(maxsize=100)` for backpressure

### Security
- Never log API keys
- Validate file paths and extensions
- Set timeouts and size limits
