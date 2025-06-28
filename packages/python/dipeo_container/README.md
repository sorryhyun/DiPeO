# DiPeO Container

Dependency injection container for DiPeO applications.

## Overview

This package provides a dependency injection container using the `dependency-injector` library. It centralizes the creation and lifecycle management of all services in the DiPeO ecosystem.

## Features

- **Service Registration**: All services are registered and wired through the container
- **Protocol Compliance**: Ensures services implement required protocols
- **Environment Configuration**: Loads configuration from environment variables
- **Lifecycle Management**: Handles initialization and cleanup of services
- **Testability**: Easy to mock services for testing

## Usage

### Server Application

```python
from dipeo_container import Container

# Create container
container = Container()

# Configure from environment
container.config.from_env()

# Initialize resources
await container.init_resources()

# Access services
execution_service = container.execution_service()
diagram_service = container.diagram_storage_service()

# Cleanup
await container.shutdown_resources()
```

### CLI Application

```python
from dipeo_container import Container

# Create container with local services
container = Container()
container.config.set("use_local_services", True)

# Initialize
await container.init_resources()

# Use services
use_case = container.execute_diagram_use_case()
result = await use_case.execute(diagram)
```

### Testing

```python
from dipeo_container import Container

# Create test container
container = Container()

# Override with mocks
container.llm_service.override(mock_llm_service)
container.file_service.override(mock_file_service)

# Run tests
service = container.execution_service()
assert service is not None
```

## Architecture

The container follows these principles:

1. **Protocol-Oriented**: All services are defined by protocols from `dipeo_core`
2. **Lazy Loading**: Services are created only when accessed
3. **Singleton Pattern**: Most services are singletons within the container
4. **Factory Pattern**: Some services (like handlers) are created per-request
5. **Configuration-Driven**: Behavior changes based on configuration

## Service Registry

The container provides all core services:

- **API Key Service**: API key management
- **LLM Service**: Language model integrations
- **File Service**: File operations
- **Conversation Service**: Memory management
- **Execution Service**: Diagram execution
- **Notion Service**: Notion integration
- **Diagram Storage Service**: Diagram persistence
- **Domain Services**: Business logic services

## Configuration

The container can be configured via:

1. **Environment Variables**: Loaded via `config.from_env()`
2. **Direct Configuration**: `config.set("key", "value")`
3. **Configuration Files**: `config.from_yaml("config.yml")`

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/
```