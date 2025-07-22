# Parser Infrastructure

This package provides parsers for various source code formats used in DiPeO's code generation pipeline.

## Architecture

The parser infrastructure follows DiPeO's clean architecture principles:

- **ports/**: Protocol definitions that abstract parser interfaces
- **typescript/**: TypeScript AST parser implementation
- Additional parsers can be added (e.g., python/, java/, etc.)

## Usage

Parsers are injected through dependency injection and implement the `ASTParserPort` protocol.

Example:
```python
from dipeo.infra.parsers.ports.ast_parser_port import ASTParserPort

class MyHandler:
    def __init__(self, parser: ASTParserPort):
        self._parser = parser
    
    async def handle(self, source: str):
        result = await self._parser.parse(
            source=source,
            extract_patterns=["interface", "type"],
            options={}
        )
        return result
```

## Available Parsers

### TypeScript Parser
- Extracts interfaces, types, enums, classes, and functions
- Uses ts-morph library for AST traversal
- Supports configurable extraction patterns