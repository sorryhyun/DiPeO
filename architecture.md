# DiPeO Ideal Architecture

## Executive Summary

DiPeO is a visual programming platform for building, executing, and monitoring AI-powered agent workflows. This document outlines the target ideal architecture that will guide the ongoing refactoring efforts to achieve a clean, maintainable, and scalable system.

## Architecture Principles

### Core Principles
1. **Clean Architecture**: Strict separation between business logic and technical details
2. **Domain-Driven Design**: Business concepts drive the structure
3. **Dependency Rule**: Dependencies point inward (Infrastructure → Application → Domain). Enforced via DI container and protocol-based interfaces
4. **Single Source of Truth**: TypeScript domain models generate all downstream code
5. **Explicit Dependencies**: No service locators or hidden dependencies
6. **Testability First**: All components easily testable in isolation
7. **Clean Repository**: No build artifacts in version control

### Technical Principles
1. **Protocol-Oriented Design**: Use Python protocols for all boundaries
2. **Immutable Domain Models**: Domain entities are immutable data structures
3. **Functional Core, Imperative Shell**: Pure business logic with side effects at boundaries
4. **Direct WebSocket Communication**: Real-time execution updates via WebSocket
5. **Type Safety**: Leverage TypeScript and Python type systems fully

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                       │
│                    Visual Diagram Editor                      │
└─────────────────────┬───────────────────┬───────────────────┘
                      │                   │
                   GraphQL             WebSocket
                      │                   │
┌─────────────────────┴───────────────────┴───────────────────┐
│                    API Gateway Layer                          │
│                 (FastAPI + Strawberry)                        │
├───────────────────────────────────────────────────────────────┤
│                  Application Layer                            │
│              (Use Cases / Orchestration)                      │
├───────────────────────────────────────────────────────────────┤
│                    Domain Layer                               │
│            (Entities / Domain Services / Ports)               │
├───────────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                          │
│        (Adapters / External Services / Persistence)           │
└───────────────────────────────────────────────────────────────┘
```

## Layered Architecture Design

### 1. Domain Layer (Core Business Logic)
**Location**: `packages/python/dipeo_domain/`

**Contents**:
- **Generated Models**: Auto-generated from TypeScript (entities, value objects, enums)
- **Domain Services**: Pure business logic services (moved from `apps/server/domains/`)
- **Ports**: Protocol interfaces for external dependencies
- **Domain Events**: BusinessEvent protocol and implementations
- **Validators**: Business rule validation

**Key Characteristics**:
- No external dependencies (only imports from protocols)
- Pure Python with type hints
- All I/O through ports (protocols)
- Immutable data structures
- Domain services depend ONLY on ports, never on infrastructure

### 2. Application Layer (Use Case Orchestration)
**Location**: `packages/python/dipeo_application/`

**Contents**:
- **Use Cases**: Complete business workflows
- **DTOs**: Data Transfer Objects for API communication
- **Application Services**: Cross-domain orchestration
- **Command/Query Handlers**: CQRS pattern implementation

**Key Characteristics**:
- Orchestrates domain services
- Manages transactions
- Handles cross-cutting concerns
- Depends only on domain layer interfaces

### 3. Infrastructure Layer (Technical Implementation)
**Location**: `packages/python/dipeo_infra/`

**Contents**:
- **External Adapters**: LLM providers, Notion, HTTP clients
- **Persistence**: File storage, database repositories
- **Messaging**: WebSocket handlers for real-time updates
- **Configuration**: Environment and config management

**Key Characteristics**:
- Implements domain ports
- Handles all I/O operations
- Contains third-party integrations
- Swappable implementations

### 4. API Layer (Transport & Presentation)
**Location**: `apps/server/src/dipeo_server/api/`

**Contents**:
- **GraphQL Schema**: Type definitions and resolvers
- **REST Endpoints**: Health checks, file uploads
- **WebSocket Handlers**: Real-time updates
- **Middleware**: Auth, logging, error handling

**Key Characteristics**:
- Thin layer, no business logic
- Maps between transport and application DTOs
- Handles serialization/deserialization
- Security and rate limiting

## Package Structure

### Monorepo Organization
```
DiPeO/
├── apps/
│   ├── server/          # FastAPI server (thin API layer only)
│   ├── web/             # React frontend
│   └── cli/             # Python CLI tool
├── packages/
│   ├── domain-models/   # TypeScript source models
│   └── python/
│       ├── dipeo_domain/        # Domain layer
│       ├── dipeo_application/   # Application layer  
│       ├── dipeo_infra/         # Infrastructure layer
│       ├── dipeo_shared/        # Shared utilities
│       └── dipeo_testing/       # Test utilities
└── tools/
    └── codegen/         # Code generation tools
```

### Detailed Package Structure

#### dipeo_domain
```
dipeo_domain/
├── models.py            # Auto-generated from TypeScript (DO NOT EDIT)
├── __generated__/       # Additional generated files
├── services/            # Domain services (moved from apps/server/domains/)
│   ├── diagram/
│   ├── execution/
│   ├── conversation/
│   ├── person/
│   └── validation/
├── ports/               # Protocol interfaces
│   ├── storage.py       # Storage port (protocol)
│   ├── llm.py           # LLM port  
│   ├── messaging.py     # WebSocket messaging port
│   ├── state.py         # State store port
│   └── integration.py   # External integration port
└── events/
    ├── base.py          # Event protocol
    └── domain_events.py # Concrete events
```

#### dipeo_application
```
dipeo_application/
├── use_cases/
│   ├── create_diagram.py
│   ├── execute_diagram.py
│   ├── manage_person.py
│   └── monitor_execution.py
├── services/
│   ├── workflow_orchestrator.py
│   ├── execution_coordinator.py
│   └── notification_service.py
├── dto/
│   ├── diagram_dto.py
│   ├── execution_dto.py
│   └── response_dto.py
└── handlers/
    ├── command_handlers.py
    └── query_handlers.py
```

#### dipeo_infra
```
dipeo_infra/
├── external/
│   ├── llm/
│   │   ├── openai_adapter.py
│   │   ├── anthropic_adapter.py
│   │   └── llm_factory.py
│   ├── notion/
│   │   └── notion_adapter.py
│   └── http/
│       └── http_client.py
├── persistence/
│   ├── file/
│   │   ├── diagram_repository.py
│   │   └── file_storage.py
│   └── memory/
│       └── in_memory_store.py
├── messaging/
│   └── websocket_publisher.py
└── config/
    ├── settings.py
    └── dependency_injection.py
```

## Dependency Injection Strategy

### Container-Based DI
```python
# dipeo_infra/config/dependency_injection.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()
    
    # Infrastructure
    file_storage = providers.Singleton(
        FileStorage,
        base_path=config.storage.base_path
    )
    
    openai_adapter = providers.Factory(
        OpenAIAdapter,
        api_key=config.openai.api_key
    )
    
    llm_factory = providers.Singleton(
        LLMFactory,
        adapters={
            'openai': openai_adapter,
            'anthropic': providers.Factory(AnthropicAdapter)
        }
    )
    
    # Domain Services (injected with port implementations)
    diagram_service = providers.Factory(
        DiagramService,
        storage=file_storage  # file_storage implements StoragePort
    )
    
    # Application Services
    create_diagram_use_case = providers.Factory(
        CreateDiagramUseCase,
        diagram_service=diagram_service,
        websocket_publisher=providers.Singleton(WebSocketPublisher)
    )
```

### Usage in API Layer
```python
# apps/server/src/dipeo_server/api/graphql/resolvers.py
from dependency_injector.wiring import Provide, inject

@strawberry.type
class Mutation:
    @strawberry.mutation
    @inject
    async def create_diagram(
        self,
        input: CreateDiagramInput,
        use_case: CreateDiagramUseCase = Provide[Container.create_diagram_use_case]
    ) -> DiagramResponse:
        result = await use_case.execute(input.to_dto())
        return DiagramResponse.from_dto(result)
```

## Node Handler Architecture

### Handler Registry Pattern
```python
# dipeo_application/handlers/registry.py
from typing import Protocol, Dict, Type, List

class NodeHandler(Protocol):
    node_type: str
    required_services: List[str]  # Services this handler needs
    
    async def execute(self, context: ExecutionContext, config: Dict) -> NodeResult:
        ...

class HandlerRegistry:
    def __init__(self, container):
        self._handlers: Dict[str, Type[NodeHandler]] = {}
        self._container = container
    
    def register(self, handler_class: Type[NodeHandler]):
        self._handlers[handler_class.node_type] = handler_class
    
    def get_handler(self, node_type: str) -> NodeHandler:
        handler_class = self._handlers[node_type]
        # Inject required services based on handler metadata
        services = self._get_services_for_handler(handler_class)
        return handler_class(**services)

# Auto-registration through decorators
def node_handler(node_type: str):
    def decorator(cls):
        cls.node_type = node_type
        handler_registry.register(cls)
        return cls
    return decorator

# Usage
@node_handler("person_job")  
class PersonJobHandler:
    required_services = ['llm_service', 'conversation_service']
    
    def __init__(self, llm_service: SupportsLLM, conversation_service: SupportsConversation):
        self.llm_service = llm_service
        self.conversation_service = conversation_service
    
    async def execute(self, context: ExecutionContext, config: Dict) -> NodeResult:
        # Implementation using injected services
```

## Code Generation Strategy

### Single Source of Truth
TypeScript models in `packages/domain-models/` generate:
1. Python domain models (Pydantic) - ✅ Currently implemented
2. GraphQL schema (SDL) - ⚠️  Currently manual, to be automated
3. TypeScript types for frontend - ✅ Via GraphQL codegen
4. Python DTOs for application layer - ❌ To be implemented
5. CLI operation types - ✅ Currently implemented

Note: Currently, some Python models are still manually maintained. The goal is to generate ALL models from TypeScript to ensure consistency.

### Generation Pipeline
```yaml
# codegen.yml
generates:
  # Python Domain Models
  packages/python/dipeo_domain/generated/:
    schema: packages/domain-models/src/**/*.ts
    plugins:
      - python-pydantic
    config:
      immutable: true
      
  # GraphQL Schema
  apps/server/schema.graphql:
    schema: packages/domain-models/src/**/*.ts
    plugins:
      - schema-ast
      
  # Python DTOs
  packages/python/dipeo_application/generated/:
    schema: apps/server/schema.graphql
    plugins:
      - python-operations
      
  # TypeScript Types
  apps/web/src/__generated__/:
    schema: apps/server/schema.graphql
    documents: apps/web/src/**/*.graphql
    plugins:
      - typescript
      - typescript-operations
      - typescript-react-apollo
```

## Testing Strategy

### Test Pyramid
1. **Unit Tests** (70%)
   - Domain logic tests (pure functions)
   - Individual handler tests
   - Service tests with mocked dependencies

2. **Integration Tests** (20%)
   - API endpoint tests
   - Database integration tests
   - External service adapter tests

3. **E2E Tests** (10%)
   - Critical user journeys
   - Diagram creation and execution flows

### Test Structure
```
tests/
├── unit/
│   ├── domain/
│   ├── application/
│   └── infra/
├── integration/
│   ├── api/
│   └── adapters/
└── e2e/
    └── scenarios/
```

### Testing Utilities
```python
# dipeo_testing/builders.py
class DiagramBuilder:
    def with_nodes(self, nodes: List[Node]) -> 'DiagramBuilder':
        ...
    
    def build(self) -> Diagram:
        ...

# dipeo_testing/fixtures.py
@pytest.fixture
def mock_llm_service():
    return Mock(spec=LLMPort)

# dipeo_testing/containers.py
class TestContainer(Container):
    # Override with test doubles
    llm_service = providers.Singleton(MockLLMService)
```

## Performance Considerations

### Optimization Strategies
1. **Lazy Loading**: Load handlers only when needed
2. **Connection Pooling**: Reuse LLM connections
3. **Caching**: Cache diagram validations and conversions
4. **Async Everywhere**: Leverage Python's async/await
5. **Batch Operations**: Group database operations

### Monitoring
1. **OpenTelemetry**: Distributed tracing
2. **Metrics**: Prometheus-compatible metrics
3. **Logging**: Structured JSON logging
4. **Health Checks**: Comprehensive health endpoints

## Security Architecture

### Security Layers
1. **API Gateway**: Rate limiting, API key validation
2. **Application**: Input validation, authorization
3. **Domain**: Business rule enforcement
4. **Infrastructure**: Encryption, secure storage

### Key Security Measures
- Environment-based configuration
- Secrets management (no hardcoded keys)
- Input sanitization
- SQL injection prevention
- XSS protection in GraphQL

## Version Control Guidelines

### Clean Repository
- **No build artifacts**: `build/`, `dist/`, `*.egg-info/` must be in `.gitignore`
- **No generated files**: Unless explicitly marked as checked-in generated files
- **No compiled code**: Python bytecode, TypeScript output
- **No dependencies**: `node_modules/`, `.venv/`, etc.

### Generated Files Policy
Files that ARE checked in:
- `packages/python/dipeo_domain/models.py` (marked with DO NOT EDIT)
- `apps/cli/src/dipeo_cli/__generated__/` (marked with DO NOT EDIT)

Files that are NOT checked in:
- Any `build/`, `dist/`, `*.egg-info/` directories
- Compiled Python files (`__pycache__/`, `*.pyc`)
- Node.js build outputs

## Deployment Architecture

### Container Strategy
```dockerfile
# Base image for all Python packages
FROM python:3.13-slim as base

# Domain layer (no external deps)
FROM base as domain
COPY packages/python/dipeo_domain /app/dipeo_domain

# Application layer
FROM domain as application
COPY packages/python/dipeo_application /app/dipeo_application

# Full server
FROM application as server
COPY apps/server /app/server
```

### Deployment Options
1. **Monolithic**: Single container with all services
2. **Microservices**: Separate execution engine
3. **Serverless**: Lambda functions for handlers
4. **Hybrid**: Core server + serverless handlers

## Conclusion

This architecture provides:
- Clear separation of concerns
- High testability
- Easy extensibility
- Performance optimization opportunities
- Strong type safety
- Excellent developer experience

The migration path allows incremental adoption while maintaining system stability. Each phase delivers value independently, reducing risk and allowing for course corrections.

## Important Notes

This document describes the **target ideal architecture** for DiPeO. The current codebase is in transition and may not fully conform to all aspects described here. See `TODO.md` for the specific migration tasks needed to achieve this architecture.

Key differences between current state and this ideal:
- ✅ Domain services have been moved to `packages/python/dipeo_domain/domains/`
- ✅ Package names have been updated: `dipeo_usecases` → `dipeo_application`, `dipeo_services` → `dipeo_infra`
- ✅ Domain services no longer directly import infrastructure components (now use ports)
- ✅ Build artifacts are properly excluded from the repository
- ✅ Model duplication has been addressed with proper extension patterns
- Not all models are generated from TypeScript yet (some manual models remain)

The migration will be done incrementally to minimize disruption while working towards this cleaner architecture.