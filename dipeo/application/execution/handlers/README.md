# DiPeO Node Handlers

## Overview

The `dipeo/application/execution/handlers` module implements **node-specific execution handlers** that process different node types during diagram execution. Each handler encapsulates the business logic for executing a specific type of node, managing inputs/outputs, and integrating with external services.

## Architecture

### Handler System Design

```
┌─────────────────────────────────┐
│     Handler Factory             │
│  (Auto-registration & Dispatch) │
└──────────┬──────────────────────┘
           │
    ┌──────▼──────┐
    │  Handler    │
    │  Registry   │
    └──────┬──────┘
           │
┌──────────┴───────────────────────┐
│       Node Handlers              │
├──────────────────────────────────┤
│ PersonJobHandler  │ LLM queries  │
│ CodeJobHandler    │ Code exec    │
│ ConditionHandler  │ Branching    │
│ ApiJobHandler     │ API calls    │
│ TemplateHandler   │ Templates    │
│ SubDiagramHandler │ Nested flows │
└──────────────────────────────────┘
```

### Handler Organization

Handlers can be organized in two patterns:

1. **Simple Handlers** - Single file implementation
2. **Complex Handlers** - Package with supporting modules

```
handlers/
├── simple_handler.py           # Simple handler
└── complex_handler/            # Complex handler package
    ├── __init__.py            # Main handler
    └── executors/             # Supporting modules
        ├── executor_a.py
        └── executor_b.py
```

## Core Components

### 1. Base Handler (`handler_base.py`)

Abstract base for all node handlers:

```python
class TypedNodeHandler(ABC, Generic[T]):
    """Base class for typed node handlers"""
    
    @property
    @abstractmethod
    def node_class(self) -> type[T]:
        """Node class this handler processes"""
        pass
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        """Node type identifier"""
        pass
    
    @property
    @abstractmethod
    def schema(self) -> type[BaseModel]:
        """Pydantic schema for node data"""
        pass
    
    async def pre_execute(self, request: ExecutionRequest[T]) -> Optional[NodeOutputProtocol]:
        """Pre-execution validation and setup.
        Returns NodeOutputProtocol to skip execution, None to proceed."""
        return None
    
    @abstractmethod
    async def execute_request(self, request: ExecutionRequest[T]) -> NodeOutputProtocol:
        """Main execution logic"""
        pass
```

### 2. Auto Registration (`auto_register.py`)

Automatic handler discovery and registration:

```python
def register_handler(handler_class: type[TypedNodeHandler]):
    """Decorator to register handlers automatically"""
    node_type = handler_class.node_type
    HANDLER_REGISTRY[node_type] = handler_class
    return handler_class

def auto_discover_handlers():
    """Automatically discover and register all handlers"""
    handlers_dir = Path(__file__).parent
    
    for path in handlers_dir.glob("**/*.py"):
        if path.name.startswith("_"):
            continue
            
        # Import module to trigger registration
        module_name = path.stem
        importlib.import_module(f"dipeo.application.execution.handlers.{module_name}")
```

### 3. Handler Factory (`handler_factory.py`)

Creates handler instances for node types:

```python
class HandlerFactory:
    """Factory for creating node handlers"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._handlers: dict[type, TypedNodeHandler] = {}
        self._initialize_handlers()
    
    def get_handler(self, node_type: type) -> TypedNodeHandler:
        """Get handler for node type"""
        if node_type not in self._handlers:
            raise HandlerNotFoundError(f"No handler for {node_type}")
        return self._handlers[node_type]
    
    def _initialize_handlers(self):
        """Initialize all registered handlers with dependencies"""
        for node_type, handler_class in HANDLER_REGISTRY.items():
            self._handlers[node_type] = handler_class(self.registry)
```

## Pre-Execute Pattern

The `pre_execute()` method provides clean separation between validation/setup and execution:

```python
class TypedNodeHandler(ABC, Generic[T]):
    async def pre_execute(self, request: ExecutionRequest[T]) -> Optional[NodeOutputProtocol]:
        """Pre-execution hook for checks and early returns.
        Returns NodeOutputProtocol to skip execution, None to proceed."""
        return None
    
    async def execute_request(self, request: ExecutionRequest[T]) -> NodeOutputProtocol:
        """Main execution logic."""
        pass
```

### Using Instance Variables

Store validated data as instance variables in `pre_execute()`:

```python
@register_handler
class ApiJobNodeHandler(TypedNodeHandler[ApiJobNode]):
    def __init__(self, api_service=None):
        self.api_service = api_service
        # Instance vars for current execution
        self._current_method = None
        self._current_headers = None
    
    async def pre_execute(self, request):
        # Validate and store in instance vars
        self._current_method = self._validate_method(request.node.method)
        self._current_headers = self._parse_headers(request.node.headers)
        
        if not self._current_method:
            return ErrorOutput(value="Invalid method", node_id=request.node.id)
        return None
    
    async def execute_request(self, request):
        # Use instance vars directly
        response = await self.api_service.call(
            method=self._current_method,
            headers=self._current_headers
        )
        return APIJobOutput(value=response.data, node_id=request.node.id)
```

## Available Node Handlers

### Core Handlers

| Handler | Location | Purpose | Key Features |
|---------|----------|---------|--------------|
| **PersonJobHandler** | `person_job.py` | LLM interactions with person context | - Manages conversation history<br>- Supports multiple LLM models<br>- Batch execution capability<br>- Max iteration checks via pre_execute() |
| **CodeJobHandler** | `code_job/` | Execute code in multiple languages | - Python, TypeScript, Bash support<br>- Sandboxed execution<br>- File or inline code<br>- Timeout management |
| **ConditionHandler** | `condition/` | Conditional branching logic | - Multiple evaluator types<br>- Expression evaluation<br>- Iteration counting<br>- Custom conditions |
| **ApiJobHandler** | `api_job.py` | External API calls | - HTTP methods support<br>- Authentication handling<br>- Retry logic<br>- JSON parsing in pre_execute() |
| **EndpointHandler** | `endpoint.py` | Data pass-through and storage | - Optional file saving<br>- Data transformation<br>- Path resolution in pre_execute() |

### Advanced Handlers

| Handler | Location | Purpose | Key Features |
|---------|----------|---------|--------------|
| **SubDiagramHandler** | `sub_diagram.py` | Execute nested diagrams | - Batch mode support<br>- Context inheritance<br>- Parallel execution |
| **TemplateJobHandler** | `template_job.py` | Template processing | - Handlebars templates<br>- Data merging<br>- Multiple template engines |
| **HookHandler** | `hook.py` | Lifecycle hooks | - Pre/post execution hooks<br>- Custom scripts<br>- Event triggering |
| **IntegratedApiHandler** | `integrated_api.py` | Specialized API integrations | - Service-specific adapters<br>- Built-in authentication |
| **DBTypedHandler** | `db_typed.py` | Database operations | - Query execution<br>- Transaction support<br>- Multiple DB types |

### Handler Organization

Handlers follow two organizational patterns:

**Simple Handler** (single file):
```
handlers/
└── person_job.py    # Complete implementation in one file
```

**Complex Handler** (package):
```
handlers/
└── code_job/
    ├── __init__.py   # Main handler with pre_execute()
    └── executors/    # Supporting modules
        ├── python_executor.py
        └── typescript_executor.py
```

## Creating Custom Handlers

### Basic Handler Template

```python
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler

@register_handler
class CustomNodeHandler(TypedNodeHandler[CustomNode]):
    """Handler for custom node type"""
    
    def __init__(self, custom_service=None):
        self.custom_service = custom_service
        # Instance vars for pre_execute pattern
        self._validated_data = None
    
    @property
    def node_class(self) -> type[CustomNode]:
        return CustomNode
    
    @property
    def node_type(self) -> str:
        return NodeType.CUSTOM.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return CustomNodeData
    
    async def pre_execute(self, request: ExecutionRequest[CustomNode]) -> Optional[NodeOutputProtocol]:
        """Validate and prepare execution"""
        # Early validation and setup
        # Store in instance variables
        # Return ErrorOutput for failures, None to proceed
        return None
    
    async def execute_request(self, request: ExecutionRequest[CustomNode]) -> NodeOutputProtocol:
        """Execute using validated data from pre_execute"""
        # Use instance variables set in pre_execute
        return DataOutput(value=result, node_id=request.node.id)
```

## Handler Lifecycle

1. **Registration**: Handlers are decorated with `@register_handler` and auto-registered on import
2. **Initialization**: Factory creates handler instances with dependencies  
3. **Pre-execution**: `pre_execute()` validates inputs and prepares data
4. **Execution**: `execute_request()` performs the main logic
5. **Post-execution**: Optional `post_execute()` for cleanup

## Error Handling

Handlers should return `ErrorOutput` for recoverable errors in `pre_execute()` or `execute_request()`:

```python
async def pre_execute(self, request):
    if not request.node.url:
        return ErrorOutput(
            value="URL is required",
            node_id=request.node.id,
            error_type="ValidationError"
        )
    return None
```

For unrecoverable errors, raise exceptions that will be caught by the execution engine.

## Best Practices

1. **Use pre_execute()** for validation and setup
2. **Store state in instance variables** between pre_execute and execute_request
3. **Return early with ErrorOutput** for validation failures
4. **Keep handlers focused** on a single node type
5. **Make I/O operations async** for better performance
6. **Test handlers in isolation** with mocked dependencies


## Future Enhancements

- **Handler Middleware**: Cross-cutting concerns (logging, metrics)
- **Handler Composition**: Combine multiple handlers
- **Dynamic Handler Loading**: Load handlers from plugins
- **Handler Versioning**: Support multiple handler versions
- **Performance Monitoring**: Built-in handler metrics