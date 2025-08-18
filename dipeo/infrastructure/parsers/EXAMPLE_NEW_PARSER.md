# Adding a New Parser - Example

This document shows how to add support for a new programming language using the refactored parser architecture.

## Example: Adding a Python Parser

### Option 1: Using the @parser_plugin Decorator

```python
# dipeo/infrastructure/parsers/python/parser.py
from dipeo.infrastructure.parsers import parser_plugin
from dipeo.domain.parsers.ports import ASTParserPort

@parser_plugin("python")
class PythonParser:
    """Python AST parser implementation."""
    
    def __init__(self, config):
        self.project_root = config.project_root
        self.cache_enabled = config.cache_enabled
        self._cache = {} if config.cache_enabled else None
    
    async def parse(self, source: str, extract_patterns: list[str], 
                   options: dict | None = None) -> dict:
        # Implementation using Python's ast module
        import ast
        tree = ast.parse(source)
        # ... extract patterns logic ...
        return {
            "ast": extracted_nodes,
            "metadata": {"success": True}
        }
```

### Option 2: Runtime Registration

```python
# In your initialization code
from dipeo.infrastructure.parsers import ParserRegistry
from my_parsers import RustParser

# Register at runtime
ParserRegistry.register_parser_class("rust", RustParser)

# Or register a factory function
def create_go_parser(config):
    return GoParser(
        project_root=config.project_root,
        cache_size=100
    )

ParserRegistry.register_parser_factory("go", create_go_parser)
```

### Option 3: Built-in Parser (Core Support)

For parsers that should be part of the core DiPeO distribution:

1. **Add parser script to resource locator:**
```python
# dipeo/infrastructure/parsers/resource_locator.py
PARSER_SCRIPTS = {
    "typescript": "typescript/ts_ast_extractor.ts",
    "python": "python/py_ast_extractor.py",  # Add this
    # ...
}
```

2. **Update the factory:**
```python
# dipeo/infrastructure/parsers/factory.py
elif language == "python":
    from .python.parser import PythonParser
    return PythonParser(
        project_root=config.project_root,
        cache_enabled=config.cache_enabled
    )
```

## Using Your New Parser

Once registered, the parser is automatically available:

```python
from dipeo.infrastructure.services.parser import get_parser_service

service = get_parser_service()

# Parse Python code
python_source = """
def hello(name: str) -> str:
    return f"Hello, {name}!"
"""

result = await service.parse(
    source=python_source,
    extract_patterns=["function", "type_hints"],
    options={"language": "python"}
)

# Or let it auto-detect from file extension
result = await service.parse_file(
    "example.py",
    extract_patterns=["class", "function"]
)
```

## Benefits of This Architecture

1. **No hard-coded paths** - Parser scripts are located dynamically
2. **Plugin support** - Add parsers without modifying core code
3. **Unified interface** - All parsers work through the same service
4. **Language auto-detection** - Based on file extensions
5. **Caching control** - Per-parser cache management
6. **Easy testing** - Mock parsers can be registered for tests

## Testing Your Parser

```python
import pytest
from dipeo.infrastructure.parsers import ParserRegistry

@pytest.fixture
def mock_parser():
    class MockParser:
        async def parse(self, source, patterns, options=None):
            return {"ast": {"test": True}, "metadata": {"success": True}}
    
    ParserRegistry.register_parser_class("test_lang", MockParser)
    yield
    ParserRegistry.unregister("test_lang")

async def test_custom_parser(mock_parser):
    service = get_parser_service()
    result = await service.parse(
        "test code",
        ["test"],
        {"language": "test_lang"}
    )
    assert result["metadata"]["success"]
```