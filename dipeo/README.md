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
from dipeo import BaseService, UnifiedExecutionContext, Person, Diagram

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

During the migration, the packages are being moved from:
- `packages/python/dipeo_core` → `dipeo/core/`
- `packages/python/dipeo_domain` → `dipeo/domain/`
- `packages/python/dipeo_diagram` → `dipeo/diagram/`
- `packages/python/dipeo_application` → `dipeo/application/`
- `packages/python/dipeo_infra` → `dipeo/infra/`
- `packages/python/dipeo_container` → `dipeo/container/`

The umbrella package ensures backward compatibility during this transition.