Looking at your backend codebase, I can see several opportunities for refactoring. Let me analyze the main issues and provide concrete suggestions:

## Major Issues to Address

### 5. **Split the LLM adapters**
Your `llm_adapters.py` contains all adapters in one file. Split them:

```
apps/server/src/llm/
├── __init__.py
├── base.py          # BaseAdapter and ChatResult
├── adapters/
│   ├── __init__.py
│   ├── claude.py
│   ├── openai.py
│   ├── gemini.py
│   └── grok.py
└── factory.py       # Adapter factory
```

### 6. **Streaming logic separation**
Create a dedicated streaming module:

```python
# apps/server/src/streaming/executor.py
class StreamingDiagramExecutor:
    """Handles diagram execution with streaming updates."""
    
    def __init__(self, diagram: dict, stream_manager: StreamManager):
        self.diagram = diagram
        self.stream_manager = stream_manager
        self.execution_id = None
        
    async def execute(self) -> AsyncGenerator[dict, None]:
        """Execute diagram and yield status updates."""
        # Move all the streaming logic from main.py here
```

### 7. **Consolidate error handling**
Create a unified error handling system:

```python
# apps/server/src/core/errors.py
from functools import wraps
from typing import Callable, Type, Dict

class ErrorHandler:
    error_mappings: Dict[Type[Exception], int] = {
        ValidationError: 400,
        APIKeyError: 401,
        FileOperationError: 403,
        DiagramExecutionError: 500,
    }
    
    @classmethod
    def handle_errors(cls, default_status: int = 500):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    status = cls.error_mappings.get(type(e), default_status)
                    return JSONResponse(
                        status_code=status,
                        content={"error": str(e), "type": type(e).__name__}
                    )
            return wrapper
        return decorator
```
