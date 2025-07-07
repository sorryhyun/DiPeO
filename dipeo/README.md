# DiPeO Umbrella Package

This is the main DiPeO package that provides unified access to all DiPeO modules.

## Installation

```bash
pip install -e dipeo
```

## Usage

The umbrella package provides several ways to import DiPeO functionality:

### Direct imports from the main package

```python
# Import specific items directly
from dipeo import BaseService, Person, Diagram
# Note: UnifiedExecutionContext moved to application layer (deprecated class)
from dipeo.application import UnifiedExecutionContext

# Import sub-modules
from dipeo import core, domain, diagram, application, infra, container
```

### Import from sub-modules

```python
# Core abstractions
from dipeo.core import BaseService, BaseExecutor, NodeHandler

# Domain models
from dipeo.domain import Person, Diagram, NodeType
from dipeo.models import Arrow, Edge  # 'models' is an alias for 'domain'

# Diagram utilities
from dipeo.diagram import UnifiedDiagramConverter, NativeJsonStrategy

# Application layer
from dipeo.application import ExecutionEngine, ApplicationContext

# Infrastructure
from dipeo.infra import LLMInfraService, ConsolidatedFileService

# Dependency injection
from dipeo.container import Container, init_resources
```

## Package Structure

The DiPeO package follows a clean architecture with the following structure:
- `dipeo/core/` - Base abstractions and protocols
- `dipeo/domain/` - Domain models and services  
- `dipeo/models/` - Generated models from TypeScript (alias for domain)
- `dipeo/diagram/` - Diagram format conversion and utilities
- `dipeo/application/` - Use cases and orchestration
- `dipeo/infra/` - Infrastructure implementations
- `dipeo/container/` - Dependency injection container

### Architecture Notes
- The core layer has no dependencies on other layers
- UnifiedExecutionContext has been moved to `dipeo.application.compatibility` for architectural compliance
- Domain models are generated from TypeScript sources in `dipeo/models/src/`