# DiPeO Core Ports

## Overview

The `dipeo/core/ports` module defines the **port interfaces** (protocols) that form the boundary between the core domain and infrastructure layers. Following **hexagonal architecture** principles, these ports enable dependency inversion, allowing the core to remain independent of infrastructure implementations.

## Architecture

### Hexagonal Architecture Pattern

```
┌─────────────────────────────────────┐
│         Core Domain                 │
│  ┌─────────────────────────────┐   │
│  │   Business Logic            │   │
│  │   (Uses Port Interfaces)    │   │
│  └─────────────┬───────────────┘   │
│                │                    │
│    ┌───────────▼───────────┐       │
│    │   Port Interfaces     │◄──────┼──── Defined Here
│    │   (Protocols)         │       │
│    └───────────▲───────────┘       │
└────────────────┼────────────────────┘
                 │
     ┌───────────▼───────────┐
     │   Infrastructure      │
     │   Adapters            │
     │   (Implements Ports)  │
     └───────────────────────┘
```

### Key Principles

1. **Dependency Inversion**: Core defines interfaces, infrastructure implements them
2. **Protocol-Based**: Uses Python's `Protocol` for structural subtyping
3. **No Infrastructure Dependencies**: Ports contain no implementation details
4. **Type Safety**: Strong typing with generics and type hints
5. **Testability**: Easy to mock/stub for testing

## Port Interfaces

### 1. LLM Service Port (`llm_service.py`)

Interface for Large Language Model interactions:

```python
class LLMServicePort(Protocol):
    """Port for LLM service operations"""
    
    async def generate(self,
                      prompt: str,
                      model: str | None = None,
                      temperature: float = 0.7,
                      max_tokens: int | None = None) -> str:
        """Generate text from LLM"""
    
    async def generate_with_conversation(self,
                                        conversation: list[Message],
                                        model: str | None = None) -> Message:
        """Generate with conversation context"""
    
    def count_tokens(self, text: str, model: str | None = None) -> int:
        """Count tokens for text"""
```

**Implementations**: OpenAI, Claude, Gemini, Ollama adapters

### 2. State Store Port (`state_store.py`)

Interface for execution state persistence:

```python
class StateStorePort(Protocol):
    """Port for state persistence operations"""
    
    async def save_execution_state(self,
                                  execution_id: str,
                                  state: ExecutionState) -> None:
        """Persist execution state"""
    
    async def load_execution_state(self,
                                  execution_id: str) -> ExecutionState | None:
        """Load execution state"""
    
    async def update_node_state(self,
                               execution_id: str,
                               node_id: str,
                               status: NodeStatus,
                               output: Any | None = None) -> None:
        """Update individual node state"""
    
    async def list_executions(self,
                             status: ExecutionStatus | None = None) -> list[ExecutionInfo]:
        """List executions with optional filtering"""
```

**Implementations**: EventBasedStateStore, InMemoryStateStore, RedisStateStore

### 3. File Service Port (`file_service.py`)

Interface for file operations:

```python
class FileServicePort(Protocol):
    """Port for file system operations"""
    
    async def read_file(self, path: str) -> str:
        """Read file contents"""
    
    async def write_file(self, path: str, content: str) -> None:
        """Write file contents"""
    
    async def exists(self, path: str) -> bool:
        """Check file existence"""
    
    async def list_directory(self, path: str) -> list[str]:
        """List directory contents"""
    
    async def delete_file(self, path: str) -> None:
        """Delete file"""
```

**Implementations**: LocalFileService, S3FileService, AzureFileService

### 4. Diagram Port (`diagram_port.py`)

Interface for diagram operations:

```python
class DiagramPort(Protocol):
    """Port for diagram management"""
    
    async def load_diagram(self, diagram_id: str) -> DomainDiagram:
        """Load diagram by ID"""
    
    async def save_diagram(self, diagram: DomainDiagram) -> str:
        """Save diagram, returns ID"""
    
    async def list_diagrams(self,
                          tags: list[str] | None = None) -> list[DiagramInfo]:
        """List available diagrams"""
    
    async def validate_diagram(self, diagram: DomainDiagram) -> ValidationResult:
        """Validate diagram structure"""
```

**Implementations**: FileDiagramService, DatabaseDiagramService

### 5. API Key Port (`apikey_port.py`)

Interface for API key management:

```python
class APIKeyPort(Protocol):
    """Port for API key operations"""
    
    def get_api_key(self, service: str) -> str | None:
        """Retrieve API key for service"""
    
    def set_api_key(self, service: str, key: str) -> None:
        """Store API key for service"""
    
    def remove_api_key(self, service: str) -> None:
        """Remove API key"""
    
    def list_services(self) -> list[str]:
        """List services with stored keys"""
```

**Implementations**: EnvironmentKeyService, VaultKeyService, FileKeyService

### 6. Message Router Port (`message_router.py`)

Interface for real-time messaging:

```python
class MessageRouterPort(Protocol):
    """Port for message routing operations"""
    
    async def publish(self,
                     channel: str,
                     message: dict[str, Any]) -> None:
        """Publish message to channel"""
    
    async def subscribe(self,
                       channel: str,
                       handler: Callable[[dict], Awaitable[None]]) -> str:
        """Subscribe to channel messages"""
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from channel"""
```

**Implementations**: WebSocketRouter, RedisRouter, InMemoryRouter

### 7. Execution Observer Port (`execution_observer.py`)

Interface for execution monitoring:

```python
class ExecutionObserver(Protocol):
    """Port for execution observation"""
    
    async def on_execution_started(self,
                                  execution_id: str,
                                  diagram_id: str) -> None:
        """Handle execution start"""
    
    async def on_node_started(self,
                             execution_id: str,
                             node_id: str) -> None:
        """Handle node start"""
    
    async def on_node_completed(self,
                               execution_id: str,
                               node_id: str,
                               output: Any) -> None:
        """Handle node completion"""
    
    async def on_execution_completed(self,
                                    execution_id: str,
                                    status: ExecutionStatus) -> None:
        """Handle execution completion"""
```

**Implementations**: LoggingObserver, MetricsObserver, WebSocketObserver

### 8. Diagram Compiler Port (`diagram_compiler.py`)

Interface for diagram compilation:

```python
class DiagramCompiler(Protocol):
    """Port for diagram compilation"""
    
    def compile(self, diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile domain diagram to executable form"""
    
    def validate_connections(self, diagram: DomainDiagram) -> list[ValidationError]:
        """Validate node connections"""
    
    def optimize(self, diagram: ExecutableDiagram) -> ExecutableDiagram:
        """Optimize compiled diagram"""
```

**Implementations**: InterfaceBasedCompiler, SimpleCompiler

### 9. Integrated API Service Port (`integrated_api_service.py`)

Interface for external API integrations:

```python
class IntegratedApiServicePort(Protocol):
    """Port for integrated API operations"""
    
    async def execute_api_call(self,
                              provider: str,
                              operation: str,
                              params: dict[str, Any]) -> dict[str, Any]:
        """Execute API call through provider"""
    
    def list_providers(self) -> list[str]:
        """List available API providers"""
    
    def get_provider_operations(self, provider: str) -> list[str]:
        """Get operations for provider"""
```

**Implementations**: NotionAPI, SlackAPI, GitHubAPI, JiraAPI

### 10. AST Parser Port (`ast_parser_port.py`)

Interface for Abstract Syntax Tree parsing:

```python
class ASTParserPort(Protocol):
    """Port for AST parsing operations"""
    
    def parse(self, code: str, language: str) -> ASTNode:
        """Parse code to AST"""
    
    def extract_functions(self, ast: ASTNode) -> list[FunctionDef]:
        """Extract function definitions"""
    
    def extract_imports(self, ast: ASTNode) -> list[ImportStatement]:
        """Extract import statements"""
    
    def transform(self, ast: ASTNode, transformers: list[ASTTransformer]) -> ASTNode:
        """Apply transformations to AST"""
```

**Implementations**: PythonASTParser, TypeScriptASTParser, JavaScriptASTParser

### 11. Diagram Converter Port (`diagram_converter.py`)

Interface for diagram format conversion:

```python
class DiagramConverterPort(Protocol):
    """Port for diagram format conversion"""
    
    def convert(self,
               diagram: Any,
               from_format: str,
               to_format: str) -> Any:
        """Convert between diagram formats"""
    
    def supports_format(self, format: str) -> bool:
        """Check if format is supported"""
    
    def detect_format(self, content: str | dict) -> str:
        """Auto-detect diagram format"""
```

**Implementations**: NativeConverter, LightConverter, ReadableConverter

## Usage Patterns

### Basic Port Usage

```python
# In core domain
class DiagramExecutor:
    def __init__(self, llm_port: LLMServicePort, state_port: StateStorePort):
        self.llm = llm_port
        self.state_store = state_port
    
    async def execute(self, diagram: ExecutableDiagram):
        # Use ports without knowing implementation
        response = await self.llm.generate(prompt)
        await self.state_store.save_execution_state(exec_id, state)
```

### Dependency Injection

```python
# In application layer
from dipeo.infrastructure.adapters import OpenAIAdapter, RedisStateStore

# Create implementations
llm_service = OpenAIAdapter(api_key="...")
state_store = RedisStateStore(redis_url="...")

# Inject into domain
executor = DiagramExecutor(llm_service, state_store)
```

### Testing with Mocks

```python
# In tests
class MockLLMService:
    async def generate(self, prompt: str, **kwargs) -> str:
        return "mock response"

class MockStateStore:
    async def save_execution_state(self, exec_id: str, state: Any):
        pass  # In-memory storage for testing

# Test domain logic without infrastructure
def test_diagram_execution():
    executor = DiagramExecutor(MockLLMService(), MockStateStore())
    result = await executor.execute(test_diagram)
    assert result.status == "completed"
```

## Creating New Ports

### Step 1: Define Protocol

```python
# dipeo/core/ports/my_service.py
from typing import Protocol

class MyServicePort(Protocol):
    """Port for my service operations"""
    
    async def operation(self, param: str) -> str:
        """Perform operation"""
        ...
```

### Step 2: Implement Adapter

```python
# dipeo/infrastructure/adapters/my_adapter.py
class MyServiceAdapter:
    """Infrastructure adapter for MyServicePort"""
    
    async def operation(self, param: str) -> str:
        # Actual implementation
        return await external_api_call(param)
```

### Step 3: Register and Use

```python
# In bootstrap
registry.register(MY_SERVICE_KEY, MyServiceAdapter())

# In domain
service = registry.resolve(MY_SERVICE_KEY)
result = await service.operation("param")
```

## Best Practices

### Port Design
1. **Keep interfaces minimal** - Only include essential operations
2. **Use async/await** - For I/O operations
3. **Return domain types** - Not infrastructure-specific types
4. **Include docstrings** - Document expected behavior
5. **Use Protocol** - For structural subtyping flexibility

### Error Handling
1. **Define domain exceptions** - Not infrastructure exceptions
2. **Document error cases** - In protocol docstrings
3. **Provide fallbacks** - Default implementations where sensible
4. **Use Result types** - For operations that can fail

### Testing
1. **Create mock implementations** - For unit testing
2. **Use in-memory adapters** - For integration testing
3. **Test protocol compliance** - Ensure adapters match protocols
4. **Isolate infrastructure** - Test adapters separately

## Migration Guidelines

### From Direct Dependencies
```python
# Before: Direct dependency
class Service:
    def __init__(self):
        self.openai = OpenAI()  # Direct infrastructure dependency
    
# After: Port-based
class Service:
    def __init__(self, llm_port: LLMServicePort):
        self.llm = llm_port  # Injected port
```

### Adding Optional Features
```python
class EnhancedPort(Protocol):
    # Required methods
    async def core_operation(self) -> str: ...
    
    # Optional methods with default
    async def enhanced_operation(self) -> str:
        return "default implementation"
```

## Dependencies

**Internal:**
- `dipeo.core.type_defs` - Core type definitions
- `dipeo.diagram_generated` - Generated types
- Python `typing.Protocol` - Protocol definitions

**External:**
- Python 3.13+ - Protocol support
- No infrastructure dependencies

## Performance Considerations

- **Async everywhere**: All I/O operations should be async
- **Batch operations**: Include batch methods where applicable
- **Caching**: Ports can include caching hints
- **Connection pooling**: Handled by adapters, not ports
- **Lazy loading**: Ports can return generators/iterators

## Future Enhancements

- **Port Composition**: Combining multiple ports
- **Port Decorators**: Cross-cutting concerns (logging, metrics)
- **Port Versioning**: Supporting multiple protocol versions
- **Port Discovery**: Runtime port availability checking
- **Port Adapters**: Automatic adapter generation from protocols