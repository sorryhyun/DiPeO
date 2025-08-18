# DiPeO Infrastructure Adapters

## Overview

The `dipeo/infrastructure/adapters` module contains **concrete implementations** of the port interfaces defined in `dipeo/application/ports` and domain-specific port files. Following the **Hexagonal Architecture** (Ports and Adapters) pattern, these adapters handle all external I/O operations, third-party integrations, and infrastructure concerns while keeping the domain independent of implementation details.

## Architecture

### Hexagonal Architecture Implementation

```
┌─────────────────────────────────────┐
│     Domain & Application Layers     │
│    (Define Port Interfaces)         │
│  ┌─────────────────────────────┐   │
│  │   Uses: LLMServicePort      │   │
│  │         StateStorePort       │   │
│  │         FileServicePort      │   │
│  └─────────────┬───────────────┘   │
└────────────────┼────────────────────┘
                 │ Dependency Inversion
     ┌───────────▼───────────┐
     │  Infrastructure Layer │
     │      (Adapters)       │
     ├───────────────────────┤
     │ OpenAIAdapter         │ ◄── Implements LLMServicePort
     │ LocalBlobAdapter      │ ◄── Implements BlobStorePort
     │ MessageRouter         │ ◄── Implements MessageRouterPort
     │ DBOperationsAdapter   │ ◄── Implements DatabasePort
     └───────────────────────┘
```

### Adapter Categories

```
adapters/
├── llm/              # Large Language Model integrations
│   ├── openai.py     # OpenAI GPT models
│   ├── claude.py     # Anthropic Claude
│   ├── gemini.py     # Google Gemini
│   └── ollama.py     # Local Ollama models
├── storage/          # File and object storage
│   ├── local_adapter.py  # Local filesystem
│   ├── s3_adapter.py     # AWS S3 compatible
│   └── artifact_adapter.py # Versioned artifacts
├── database/         # Database operations
│   └── db_adapter.py # SQLite persistence
├── messaging/        # Event distribution
│   └── message_router.py # Real-time messaging
├── http/             # External API services
│   └── api_service.py # HTTP client adapter
└── parsers/          # Code parsing
    └── typescript/   # TypeScript AST parser
```

## Adapter Implementations

### 1. LLM Adapters

All LLM adapters extend `BaseLLMAdapter` and implement consistent interfaces:

#### OpenAI Adapter (`llm/openai.py`)

```python
class ChatGPTAdapter(BaseLLMAdapter):
    """OpenAI GPT models with full feature support"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        # Supports: gpt-4o, gpt-4.1, gpt-5-nano
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def supports_tools(self) -> bool:
        """Check if model supports function calling"""
        return 'gpt-4o' in self.model_name
    
    async def chat(self, messages: list[dict], **kwargs) -> ChatResult:
        """Execute chat with retry logic and error handling"""
        # Features:
        # - Automatic retries with exponential backoff
        # - Token usage tracking
        # - Tool/function calling
        # - Response streaming
        # - Structured output with Pydantic models
```

**Key Features:**
- Retry logic with exponential backoff
- Token counting and usage tracking
- Tool calling (web search, image generation)
- Response streaming support
- Structured output via Pydantic models

#### Claude Adapter (`llm/claude.py`)

```python
class ClaudeAdapter(BaseLLMAdapter):
    """Anthropic Claude models"""
    
    async def chat(self, messages: list[dict], **kwargs) -> ChatResult:
        # Supports: claude-3-opus, claude-3-sonnet
        # Features: Long context, constitutional AI
```

#### Gemini Adapter (`llm/gemini.py`)

```python
class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini models"""
    
    async def chat(self, messages: list[dict], **kwargs) -> ChatResult:
        # Supports: gemini-pro, gemini-ultra
        # Features: Multimodal, function calling
```

### 2. Storage Adapters

Storage adapters implement `BlobStorePort` and `FileSystemPort`:

#### Local Storage (`storage/local_adapter.py`)

```python
class LocalBlobAdapter(BaseService, BlobStorePort):
    """Local filesystem with versioning support"""
    
    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self._versions_dir = base_path / ".versions"
    
    async def put(self, key: str, data: bytes, metadata: dict | None = None) -> str:
        """Store with automatic versioning"""
        version = self._compute_version(data)  # SHA256 hash
        
        # Store current version
        async with aiofiles.open(object_path, "wb") as f:
            await f.write(data)
        
        # Archive version
        version_path = self._get_version_path(key, version)
        async with aiofiles.open(version_path, "wb") as f:
            await f.write(data)
        
        return version
    
    async def get(self, key: str, version: str | None = None) -> BinaryIO:
        """Retrieve specific version or latest"""
        if version:
            path = self._get_version_path(key, version)
        else:
            path = self._get_object_path(key)
        return await aiofiles.open(path, "rb")
```

**Features:**
- Automatic versioning with SHA256
- Metadata storage (.meta files)
- Async file operations
- Directory auto-creation

#### S3 Storage (`storage/s3_adapter.py`)

```python
class S3Adapter(BaseService, BlobStorePort):
    """AWS S3 compatible storage"""
    
    async def put(self, key: str, data: bytes) -> str:
        """Upload to S3 with metadata"""
        response = await self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            Metadata={"version": version}
        )
        return response["ETag"]
```

### 3. Database Adapter

#### SQLite Operations (`database/db_adapter.py`)

```python
class DBOperationsAdapter:
    """Database operations with domain service integration"""
    
    def __init__(self,
                file_system: FileSystemPort,
                domain_service: DBOperationsDomainService,
                validation_service: DataValidator):
        self.file_system = file_system
        self.domain_service = domain_service
        self.validation_service = validation_service
    
    async def execute_operation(self,
                               db_name: str,
                               operation: str,
                               value: Any = None) -> dict[str, Any]:
        """Execute validated database operation"""
        # Validate operation
        self.validation_service.validate_operation(operation)
        
        # Operations: read, write, append, prompt
        if operation == "read":
            return await self._read_db(file_path)
        elif operation == "write":
            return await self._write_db(file_path, value)
```

**Features:**
- JSON-based persistence
- Operation validation
- Atomic writes
- Backup on write

### 4. Message Router

#### Real-time Event Distribution (`messaging/message_router.py`)

```python
class MessageRouter(MessageRouterPort):
    """Central hub for real-time event distribution"""
    
    def __init__(self):
        self.execution_subscriptions: dict[str, set[str]] = {}
        self.connection_health: dict[str, ConnectionHealth] = {}
        
        # Event buffering for late connections
        self._event_buffer: dict[str, list[dict]] = {}
        self._buffer_max_size = 50
        
        # Batching for performance
        self._batch_queue: dict[str, list[dict]] = {}
        self._batch_interval = 0.1  # 100ms
    
    async def publish_event(self, execution_id: str, event: dict) -> None:
        """Publish event to all subscribers"""
        # Add to buffer for late connections
        self._buffer_event(execution_id, event)
        
        # Batch events for performance
        await self._queue_for_batch(execution_id, event)
    
    async def subscribe_connection_to_execution(self,
                                               connection_id: str,
                                               execution_id: str) -> None:
        """Subscribe to execution events"""
        # Send buffered events to catch up
        buffered = self._get_buffered_events(execution_id)
        for event in buffered:
            await self._send_to_connection(connection_id, event)
        
        # Add to active subscriptions
        self.execution_subscriptions[execution_id].add(connection_id)
```

**Key Features:**
- Event buffering (last 50 events, 5-minute TTL)
- Batch broadcasting (100ms intervals)
- Connection health monitoring
- Backpressure handling (queue size limits)
- Automatic cleanup of failed connections

### 5. HTTP/API Service

#### External API Integration (`http/api_service.py`)

```python
class IntegratedApiService(IntegratedApiServicePort):
    """Unified interface for external APIs"""
    
    def __init__(self):
        self.providers = {
            "notion": NotionProvider,
            "slack": SlackProvider,
            "github": GitHubProvider,
            "jira": JiraProvider
        }
    
    async def execute_api_call(self,
                              provider: str,
                              operation: str,
                              params: dict) -> dict:
        """Execute API call through provider"""
        provider_instance = self._get_provider(provider)
        return await provider_instance.execute(operation, params)
```

### 6. Code Parsers

#### TypeScript Parser (`parsers/typescript/`)

```python
class TypeScriptParser:
    """AST parsing for TypeScript code"""
    
    async def parse(self,
                   source_code: str,
                   extract_patterns: list[str]) -> ParseResult:
        """Parse TypeScript and extract patterns"""
        # Patterns: interface, type, class, function, enum
        
        # Use Node.js subprocess for parsing
        result = await self._run_parser_process(source_code, patterns)
        
        return ParseResult(
            interfaces=result.interfaces,
            types=result.types,
            classes=result.classes
        )
```

**Features:**
- Interface extraction
- Type alias extraction
- Class and function parsing
- Enum and constant extraction
- Cross-platform support

## Usage Patterns

### Basic Adapter Usage

```python
# 1. Create adapter instance
adapter = OpenAIAdapter(
    model_name="gpt-4.1-nano",
    api_key=os.getenv("OPENAI_API_KEY")
)

# 2. Initialize if needed
await adapter.initialize()

# 3. Use adapter
result = await adapter.chat(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7
)
```

### Dependency Injection

```python
# In service container
class ServiceContainer:
    def __init__(self):
        # Create adapters
        self.llm_adapter = OpenAIAdapter(model, key)
        self.storage_adapter = LocalBlobAdapter(base_path)
        self.message_router = MessageRouter()
        
        # Inject into services
        self.execution_service = ExecutionService(
            llm=self.llm_adapter,
            storage=self.storage_adapter,
            router=self.message_router
        )
```

### Testing with Mock Adapters

```python
class MockLLMAdapter:
    """Mock adapter for testing"""
    
    async def chat(self, messages: list[dict], **kwargs) -> ChatResult:
        return ChatResult(
            text="Mock response",
            model="mock-model",
            usage={"total_tokens": 10}
        )

# Use in tests
def test_execution():
    service = ExecutionService(llm=MockLLMAdapter())
    result = await service.execute()
    assert result.success
```

## Creating New Adapters

### Step 1: Implement Port Interface

```python
# dipeo/infrastructure/adapters/new_service/my_adapter.py
from dipeo.application.ports import MyServicePort  # or from dipeo.domain.your_domain.ports

class MyAdapter(MyServicePort):
    """Concrete implementation of MyServicePort"""
    
    def __init__(self, config: dict):
        self.config = config
        self._client = None
    
    async def initialize(self) -> None:
        """Initialize connection/resources"""
        self._client = await create_client(self.config)
    
    async def operation(self, param: str) -> str:
        """Implement port operation"""
        try:
            result = await self._client.call(param)
            return self._transform_result(result)
        except ExternalError as e:
            raise DomainError(f"Operation failed: {e}")
```

### Step 2: Add Error Handling

```python
class ResilientAdapter(MyServicePort):
    """Adapter with retry and circuit breaker"""
    
    async def operation(self, param: str) -> str:
        for attempt in range(self.max_retries):
            try:
                return await self._try_operation(param)
            except TemporaryError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise PermanentError("Max retries exceeded")
```

### Step 3: Register in Container

```python
# In dependency injection container
def create_my_adapter():
    return MyAdapter(
        config={
            "url": settings.my_service_url,
            "timeout": settings.my_service_timeout
        }
    )

# Register
container.register("my_adapter", create_my_adapter)
```

## Best Practices

### 1. Error Handling

Always wrap external errors in domain exceptions:

```python
try:
    result = await external_api.call()
except RequestException as e:
    # Don't leak infrastructure exceptions
    raise DomainError(f"API call failed: {e}") from e
```

### 2. Resource Management

Use async context managers:

```python
class ConnectionAdapter:
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, *args):
        await self.disconnect()
```

### 3. Configuration

Use settings from config module:

```python
from dipeo.infrastructure.config import get_settings

class MyAdapter:
    def __init__(self):
        settings = get_settings()
        self.timeout = settings.adapter_timeout
        self.retry_count = settings.adapter_retries
```

### 4. Logging

Log operations for debugging:

```python
logger = logging.getLogger(__name__)

class MyAdapter:
    async def operation(self, param):
        logger.debug(f"Starting operation with {param}")
        try:
            result = await self._execute(param)
            logger.info(f"Operation successful: {result.id}")
            return result
        except Exception as e:
            logger.error(f"Operation failed: {e}")
            raise
```

### 5. Testing

Provide in-memory implementations:

```python
class InMemoryStorageAdapter(BlobStorePort):
    def __init__(self):
        self.storage = {}
    
    async def put(self, key: str, data: bytes) -> str:
        self.storage[key] = data
        return hashlib.sha256(data).hexdigest()
    
    async def get(self, key: str) -> BinaryIO:
        return io.BytesIO(self.storage[key])
```

## Performance Optimization

### Connection Pooling

```python
class PooledAdapter:
    def __init__(self, pool_size: int = 10):
        self._pool = asyncio.Queue(maxsize=pool_size)
        self._initialize_pool()
    
    async def _get_connection(self):
        return await self._pool.get()
    
    async def _return_connection(self, conn):
        await self._pool.put(conn)
```

### Caching

```python
class CachedAdapter:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def get_with_cache(self, key: str):
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["time"] < self._cache_ttl:
                return entry["value"]
        
        value = await self._fetch(key)
        self._cache[key] = {"value": value, "time": time.time()}
        return value
```

### Batching

```python
class BatchingAdapter:
    async def process_batch(self, items: list):
        # Process in chunks
        chunk_size = 100
        results = []
        
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            chunk_results = await asyncio.gather(
                *[self.process_item(item) for item in chunk]
            )
            results.extend(chunk_results)
        
        return results
```

## Monitoring and Metrics

### Health Checks

```python
class MonitoredAdapter:
    async def health_check(self) -> dict:
        """Check adapter health"""
        return {
            "status": "healthy" if self._connected else "unhealthy",
            "latency": self._avg_latency,
            "error_rate": self._error_count / self._total_requests,
            "last_error": self._last_error
        }
```

### Metrics Collection

```python
class MetricsAdapter:
    def __init__(self):
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "latency": []
        }
    
    async def operation(self, param):
        start = time.time()
        try:
            result = await self._execute(param)
            self.metrics["requests"] += 1
            return result
        except Exception as e:
            self.metrics["errors"] += 1
            raise
        finally:
            self.metrics["latency"].append(time.time() - start)
```

## Migration Guide

### From Direct Dependencies to Adapters

```python
# Before: Direct dependency
class Service:
    def __init__(self):
        import openai
        self.client = openai.Client()  # Direct dependency
    
    async def process(self):
        response = self.client.chat.completions.create(...)

# After: Port-based with adapter
class Service:
    def __init__(self, llm_port: LLMServicePort):
        self.llm = llm_port  # Injected port
    
    async def process(self):
        response = await self.llm.chat(messages=[...])
```

## Common Issues and Solutions

### 1. "Adapter not initialized"

**Solution:** Ensure initialization in startup:
```python
adapter = MyAdapter()
await adapter.initialize()  # Don't forget this!
```

### 2. "Connection timeout"

**Solution:** Configure timeouts appropriately:
```python
adapter = HttpAdapter(timeout=30)  # Increase timeout
```

### 3. "Rate limit exceeded"

**Solution:** Implement backoff strategy:
```python
async def with_rate_limit(self):
    await self.rate_limiter.acquire()
    try:
        return await self.operation()
    finally:
        self.rate_limiter.release()
```

## Dependencies

**Internal:**
- `dipeo.application.ports` - Application-level port interfaces
- `dipeo.domain.*/ports` - Domain-specific port interfaces
- `dipeo.domain.base.exceptions` - Base exceptions
- `dipeo.infrastructure.config` - Configuration management

**External:**
- `aiofiles` - Async file operations
- `openai` - OpenAI API client
- `anthropic` - Claude API client
- `google.generativeai` - Gemini API
- `boto3` - AWS S3 operations
- `httpx` - Async HTTP client

## Testing

### Unit Tests

```python
@pytest.mark.asyncio
async def test_storage_adapter():
    adapter = InMemoryStorageAdapter()
    
    # Test put
    version = await adapter.put("key", b"data")
    assert version is not None
    
    # Test get
    data = await adapter.get("key")
    assert data.read() == b"data"
```

### Integration Tests

```python
@pytest.mark.integration
async def test_real_storage():
    adapter = LocalBlobAdapter("/tmp/test")
    await adapter.initialize()
    
    # Test with real filesystem
    version = await adapter.put("test.txt", b"content")
    retrieved = await adapter.get("test.txt")
    assert retrieved.read() == b"content"
```

## Future Enhancements

- **Redis Adapter**: For distributed caching
- **Kafka Adapter**: For event streaming
- **PostgreSQL Adapter**: For relational data
- **Elasticsearch Adapter**: For search functionality
- **Prometheus Adapter**: For metrics export
- **GraphQL Subscription Adapter**: For real-time updates
- **WebSocket Adapter**: For bidirectional communication
- **gRPC Adapter**: For high-performance RPC