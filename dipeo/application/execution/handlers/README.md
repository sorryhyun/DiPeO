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
from abc import ABC, abstractmethod

class TypedNodeHandler(ABC, Generic[T]):
    """Base class for typed node handlers"""
    
    @abstractmethod
    async def execute_request(self, 
                            request: ExecutionRequest[T]) -> NodeOutputProtocol:
        """Execute the node with given request"""
        pass
    
    @property
    @abstractmethod
    def node_type(self) -> type[T]:
        """Return the node type this handler processes"""
        pass
    
    async def validate_inputs(self, inputs: dict[str, Any]) -> ValidationResult:
        """Validate node inputs before execution"""
        return ValidationResult(is_valid=True)
    
    async def prepare_context(self, request: ExecutionRequest) -> dict[str, Any]:
        """Prepare execution context"""
        return {}
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

## Node Handler Implementations

### 1. PersonJob Handler (`person_job/`)

Handles LLM interaction nodes:

```python
@register_handler
class PersonJobNodeHandler(TypedNodeHandler[PersonJobNode]):
    """Handler for PersonJob nodes - LLM interactions"""
    
    def __init__(self, registry: ServiceRegistry):
        self.llm_service = registry.resolve(LLM_SERVICE)
        self.person_manager = registry.resolve(PERSON_MANAGER)
        self.conversation_manager = registry.resolve(CONVERSATION_MANAGER)
    
    async def execute_request(self, request: ExecutionRequest[PersonJobNode]) -> ConversationOutput:
        """Execute LLM query with person context"""
        node = request.node
        
        # Get or create person
        person = await self.person_manager.get_or_create(node.person_id)
        
        # Build prompt with context
        prompt = self._build_prompt(node.prompt, request.inputs, person)
        
        # Get LLM response
        response = await self.llm_service.generate_with_conversation(
            conversation=person.conversation.messages,
            prompt=prompt,
            model=node.model or person.default_model
        )
        
        # Update conversation
        person.conversation.add_message(response)
        
        return ConversationOutput(
            value=response.content,
            messages=person.conversation.messages,
            node_id=node.id,
            person_id=person.id
        )
```

**Batch Executor** (`person_job/batch_executor.py`):
```python
class PersonJobBatchExecutor:
    """Executes PersonJob for multiple inputs"""
    
    async def execute_batch(self, 
                          node: PersonJobNode,
                          batch_inputs: list[dict]) -> list[ConversationOutput]:
        """Process batch of inputs in parallel"""
        tasks = [
            self._execute_single(node, inputs)
            for inputs in batch_inputs
        ]
        return await asyncio.gather(*tasks)
```

### 2. CodeJob Handler (`code_job/`)

Executes code in various languages:

```python
@register_handler
class CodeJobNodeHandler(TypedNodeHandler[CodeJobNode]):
    """Handler for code execution nodes"""
    
    def __init__(self, registry: ServiceRegistry):
        self.executors = {
            "python": PythonExecutor(),
            "typescript": TypeScriptExecutor(),
            "bash": BashExecutor()
        }
    
    async def execute_request(self, request: ExecutionRequest[CodeJobNode]) -> DataOutput:
        """Execute code in specified language"""
        node = request.node
        executor = self.executors.get(node.language)
        
        if not executor:
            raise UnsupportedLanguageError(node.language)
        
        # Prepare execution environment
        context = self._prepare_context(request.inputs)
        
        # Execute code
        result = await executor.execute(
            code=node.code,
            context=context,
            timeout=node.timeout
        )
        
        return DataOutput(
            value=result.output,
            node_id=node.id,
            metadata={"language": node.language, "execution_time": result.execution_time}
        )
```

**Language Executors** (`code_job/executors/`):
```python
class PythonExecutor(BaseExecutor):
    """Python code executor"""
    
    async def execute(self, code: str, context: dict, timeout: int) -> ExecutionResult:
        """Execute Python code in sandboxed environment"""
        # Create isolated namespace
        namespace = {"__builtins__": safe_builtins, **context}
        
        # Execute with timeout
        try:
            exec(compile(code, "<string>", "exec"), namespace)
            return ExecutionResult(
                output=namespace.get("result"),
                success=True
            )
        except TimeoutError:
            return ExecutionResult(success=False, error="Timeout")
```

### 3. Condition Handler (`condition/`)

Evaluates conditions and handles branching:

```python
@register_handler
class ConditionNodeHandler(TypedNodeHandler[ConditionNode]):
    """Handler for conditional branching"""
    
    def __init__(self, registry: ServiceRegistry):
        self.evaluators = {
            "expression": ExpressionEvaluator(),
            "max_iterations": MaxIterationsEvaluator(),
            "nodes_executed": NodesExecutedEvaluator(),
            "custom": CustomExpressionEvaluator()
        }
    
    async def execute_request(self, request: ExecutionRequest[ConditionNode]) -> ConditionOutput:
        """Evaluate condition and determine branch"""
        node = request.node
        evaluator = self.evaluators.get(node.condition_type, "expression")
        
        # Evaluate condition
        result = await evaluator.evaluate(
            expression=node.expression,
            context=request.inputs,
            execution_context=request.execution_context
        )
        
        return ConditionOutput(
            value=result,
            branch="true" if result else "false",
            node_id=node.id,
            metadata={"condition_type": node.condition_type}
        )
```

**Condition Evaluators** (`condition/evaluators/`):
```python
class MaxIterationsEvaluator(BaseEvaluator):
    """Evaluates max iteration conditions"""
    
    async def evaluate(self, expression: str, context: dict, execution_context: ExecutionContext) -> bool:
        """Check if max iterations reached"""
        node_id = context.get("node_id")
        max_iterations = int(expression)
        current_iterations = execution_context.get_iteration_count(node_id)
        
        return current_iterations >= max_iterations
```

### 4. API Job Handler (`api_job.py`)

Handles external API calls:

```python
@register_handler
class ApiJobNodeHandler(TypedNodeHandler[ApiJobNode]):
    """Handler for API call nodes"""
    
    def __init__(self, registry: ServiceRegistry):
        self.http_client = registry.resolve(HTTP_CLIENT)
        self.api_key_service = registry.resolve(API_KEY_SERVICE)
    
    async def execute_request(self, request: ExecutionRequest[ApiJobNode]) -> DataOutput:
        """Execute API call"""
        node = request.node
        
        # Prepare request
        headers = self._prepare_headers(node)
        body = self._prepare_body(node, request.inputs)
        
        # Execute with retry logic
        response = await self._execute_with_retry(
            method=node.method,
            url=node.endpoint,
            headers=headers,
            json=body,
            max_retries=node.max_retries
        )
        
        return DataOutput(
            value=response.json(),
            node_id=node.id,
            metadata={"status_code": response.status_code}
        )
```

### 5. Template Job Handler (`template_job.py`)

Processes templates with data:

```python
@register_handler
class TemplateJobNodeHandler(TypedNodeHandler[TemplateJobNode]):
    """Handler for template processing"""
    
    def __init__(self, registry: ServiceRegistry):
        self.template_service = registry.resolve(TEMPLATE_SERVICE)
    
    async def execute_request(self, request: ExecutionRequest[TemplateJobNode]) -> TextOutput:
        """Process template with data"""
        node = request.node
        
        # Merge node data with inputs
        template_data = {**node.default_data, **request.inputs}
        
        # Process template
        result = await self.template_service.process(
            template=node.template,
            data=template_data,
            engine=node.template_engine
        )
        
        return TextOutput(
            value=result,
            node_id=node.id
        )
```

### 6. SubDiagram Handler (`sub_diagram/`)

Executes nested diagrams:

```python
@register_handler
class SubDiagramNodeHandler(TypedNodeHandler[SubDiagramNode]):
    """Handler for nested diagram execution"""
    
    def __init__(self, registry: ServiceRegistry):
        self.diagram_service = registry.resolve(DIAGRAM_SERVICE)
        self.execution_engine = registry.resolve(EXECUTION_ENGINE)
    
    async def execute_request(self, request: ExecutionRequest[SubDiagramNode]) -> DataOutput:
        """Execute nested diagram"""
        node = request.node
        
        # Load sub-diagram
        sub_diagram = await self.diagram_service.load(node.diagram_id)
        
        # Execute with parent context
        result = await self.execution_engine.execute(
            diagram=sub_diagram,
            inputs=request.inputs,
            parent_context=request.execution_context
        )
        
        return DataOutput(
            value=result.outputs,
            node_id=node.id,
            metadata={"sub_execution_id": result.execution_id}
        )
```

## Creating Custom Handlers

### Step 1: Define Handler Class

```python
from dipeo.application.execution.handlers import TypedNodeHandler, register_handler

@register_handler
class CustomNodeHandler(TypedNodeHandler[CustomNode]):
    """Handler for custom node type"""
    
    def __init__(self, registry: ServiceRegistry):
        super().__init__(registry)
        # Initialize dependencies
        self.custom_service = registry.resolve(CUSTOM_SERVICE)
    
    @property
    def node_type(self) -> type[CustomNode]:
        return CustomNode
    
    async def execute_request(self, request: ExecutionRequest[CustomNode]) -> NodeOutputProtocol:
        """Execute custom node logic"""
        node = request.node
        
        # Custom execution logic
        result = await self.custom_service.process(
            data=request.inputs,
            config=node.config
        )
        
        return DataOutput(
            value=result,
            node_id=node.id
        )
```

### Step 2: Complex Handler with Executors

```python
# handlers/custom_handler/__init__.py
@register_handler
class ComplexHandler(TypedNodeHandler[ComplexNode]):
    """Complex handler with multiple executors"""
    
    def __init__(self, registry: ServiceRegistry):
        from .executors import ExecutorA, ExecutorB
        
        self.executors = {
            "type_a": ExecutorA(),
            "type_b": ExecutorB()
        }
    
    async def execute_request(self, request: ExecutionRequest[ComplexNode]) -> NodeOutputProtocol:
        executor = self.executors[request.node.executor_type]
        return await executor.execute(request)

# handlers/custom_handler/executors/executor_a.py
class ExecutorA:
    """Specific executor implementation"""
    
    async def execute(self, request: ExecutionRequest) -> NodeOutputProtocol:
        # Implementation
        pass
```

## Handler Lifecycle

### 1. Registration Phase
```python
# Automatic registration on import
@register_handler
class MyHandler(TypedNodeHandler[MyNode]):
    pass

# Handler is now in HANDLER_REGISTRY
```

### 2. Initialization Phase
```python
# Factory initializes with dependencies
factory = HandlerFactory(service_registry)
handler = factory.get_handler(MyNode)
```

### 3. Execution Phase
```python
# Engine calls handler
request = ExecutionRequest(
    node=my_node,
    inputs=resolved_inputs,
    execution_context=context
)
output = await handler.execute_request(request)
```

## Error Handling

### Handler Exceptions

```python
class HandlerError(Exception):
    """Base handler exception"""
    pass

class HandlerNotFoundError(HandlerError):
    """Handler not found for node type"""
    pass

class HandlerExecutionError(HandlerError):
    """Error during handler execution"""
    
    def __init__(self, handler: str, original_error: Exception):
        self.handler = handler
        self.original_error = original_error
        super().__init__(f"Handler {handler} failed: {original_error}")
```

### Error Recovery

```python
class ResilientHandler(TypedNodeHandler[T]):
    """Handler with error recovery"""
    
    async def execute_request(self, request: ExecutionRequest[T]) -> NodeOutputProtocol:
        try:
            return await self._execute_internal(request)
        except TemporaryError as e:
            # Retry with backoff
            await asyncio.sleep(self._get_backoff_time())
            return await self._execute_internal(request)
        except PermanentError as e:
            # Return error output
            return ErrorOutput(
                error=str(e),
                node_id=request.node.id
            )
```

## Testing Handlers

### Unit Testing

```python
async def test_person_job_handler():
    """Test PersonJob handler"""
    # Mock dependencies
    mock_llm = Mock(spec=LLMServicePort)
    mock_llm.generate.return_value = "test response"
    
    registry = ServiceRegistry()
    registry.register(LLM_SERVICE, mock_llm)
    
    # Create handler
    handler = PersonJobNodeHandler(registry)
    
    # Create request
    node = PersonJobNode(id="test", prompt="test prompt")
    request = ExecutionRequest(node=node, inputs={})
    
    # Execute
    output = await handler.execute_request(request)
    
    assert output.value == "test response"
    mock_llm.generate.assert_called_once()
```

### Integration Testing

```python
async def test_handler_integration():
    """Test handler with real dependencies"""
    # Setup test environment
    registry = create_test_registry()
    factory = HandlerFactory(registry)
    
    # Test multiple handlers
    for node_type in [PersonJobNode, CodeJobNode, ConditionNode]:
        handler = factory.get_handler(node_type)
        assert handler is not None
        
        # Test execution
        test_node = create_test_node(node_type)
        request = ExecutionRequest(node=test_node, inputs={})
        output = await handler.execute_request(request)
        assert not output.has_error()
```

## Performance Optimization

### Caching

```python
class CachedHandler(TypedNodeHandler[T]):
    """Handler with result caching"""
    
    def __init__(self, registry: ServiceRegistry):
        super().__init__(registry)
        self._cache = {}
    
    async def execute_request(self, request: ExecutionRequest[T]) -> NodeOutputProtocol:
        cache_key = self._get_cache_key(request)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await self._execute_internal(request)
        self._cache[cache_key] = result
        return result
```

### Parallel Execution

```python
class ParallelHandler(TypedNodeHandler[T]):
    """Handler with parallel processing"""
    
    async def execute_batch(self, requests: list[ExecutionRequest[T]]) -> list[NodeOutputProtocol]:
        """Execute multiple requests in parallel"""
        tasks = [self.execute_request(req) for req in requests]
        return await asyncio.gather(*tasks)
```

## Dependencies

**Internal:**
- `dipeo.core.execution` - Execution contracts
- `dipeo.diagram_generated` - Node types
- `dipeo.application.registry` - Service registry

**External:**
- Python 3.13+ asyncio
- `typing` - Type hints
- `dataclasses` - Data structures

## Best Practices

1. **Single Responsibility**: Each handler handles one node type
2. **Dependency Injection**: Use registry for all dependencies
3. **Error Handling**: Gracefully handle and report errors
4. **Async First**: All I/O operations should be async
5. **Type Safety**: Use typed handlers and outputs
6. **Testing**: Unit test handlers in isolation
7. **Documentation**: Document handler behavior and requirements

## Future Enhancements

- **Handler Middleware**: Cross-cutting concerns (logging, metrics)
- **Handler Composition**: Combine multiple handlers
- **Dynamic Handler Loading**: Load handlers from plugins
- **Handler Versioning**: Support multiple handler versions
- **Performance Monitoring**: Built-in handler metrics