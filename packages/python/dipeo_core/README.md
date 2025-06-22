# DiPeO Core

Core abstractions and base classes for the DiPeO (Diagrammed People & Organizations) system.

## Overview

This package provides the foundational abstractions used by both the DiPeO server and CLI:

- **Base Services**: Abstract base classes and protocols for service implementations
- **Execution Types**: Core types for diagram execution context and runtime
- **Error Hierarchy**: Unified error taxonomy for consistent error handling

## Installation

```bash
pip install dipeo-core
```

## Usage

```python
from dipeo_core.base import BaseService
from dipeo_core.execution.types import ExecutionContext
from dipeo_core.errors.taxonomy import DiPeOError

# Implement your own service
class MyService(BaseService):
    async def initialize(self) -> None:
        # Service initialization logic
        pass
```

## Development

This package is part of the DiPeO monorepo. See the main repository for development instructions.