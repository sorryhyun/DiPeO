# DiPeO Ideal Architecture

## Executive Summary

DiPeO is a visual programming platform for building, executing, and monitoring AI-powered agent workflows. This document outlines an ideal architecture that addresses current structural issues while maintaining the system's flexibility and extensibility.

## Architecture Principles

### Core Principles
1. **Clean Architecture**: Strict separation between business logic and technical details
2. **Domain-Driven Design**: Business concepts drive the structure
3. **Dependency Rule**: Dependencies point inward (Infrastructure → Application → Domain)
4. **Single Source of Truth**: TypeScript domain models generate all downstream code
5. **Explicit Dependencies**: No service locators or hidden dependencies
6. **Testability First**: All components easily testable in isolation

### Technical Principles
1. **Protocol-Oriented Design**: Use Python protocols for all boundaries
2. **Immutable Domain Models**: Domain entities are immutable data structures
3. **Functional Core, Imperative Shell**: Pure business logic with side effects at boundaries
4. **Event-Driven Communication**: Loose coupling between components
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
- **Entities**: Immutable domain objects (Diagram, Node, Person, Execution)
- **Value Objects**: DiagramId, NodeId, ExecutionStatus
- **Domain Services**: Pure business logic services
- **Ports**: Interfaces for external dependencies (protocols)
- **Domain Events**: BusinessEvent protocol and implementations

**Key Characteristics**:
- No external dependencies
- Pure Python with type hints
- All I/O through ports (protocols)
- Immutable data structures

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
**Location**: `packages/python/dipeo_infrastructure/`

**Contents**:
- **External Adapters**: LLM providers, Notion, HTTP clients
- **Persistence**: File storage, database repositories
- **Messaging**: Event bus, WebSocket handlers
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
│       ├── dipeo_infrastructure/# Infrastructure layer
│       ├── dipeo_shared/        # Shared utilities
│       └── dipeo_testing/       # Test utilities
└── tools/
    └── codegen/         # Code generation tools
```

### Detailed Package Structure

#### dipeo_domain
```
dipeo_domain/
├── entities/
│   ├── diagram.py       # Diagram entity
│   ├── node.py          # Node entities
│   ├── person.py        # Person entity
│   └── execution.py     # Execution entity
├── value_objects/
│   ├── ids.py           # DiagramId, NodeId, etc.
│   ├── config.py        # Configuration value objects
│   └── status.py        # Status enums
├── services/
│   ├── diagram_service.py
│   ├── execution_service.py
│   └── validation_service.py
├── ports/
│   ├── storage.py       # Storage port (protocol)
│   ├── llm.py           # LLM port
│   ├── notification.py  # Notification port
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

#### dipeo_infrastructure
```
dipeo_infrastructure/
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
│   ├── event_bus.py
│   └── websocket_publisher.py
└── config/
    ├── settings.py
    └── dependency_injection.py
```

## Dependency Injection Strategy

### Container-Based DI
```python
# dipeo_infrastructure/config/dependency_injection.py
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
    
    # Domain Services
    diagram_service = providers.Factory(
        DiagramService,
        storage=file_storage
    )
    
    # Application Services
    create_diagram_use_case = providers.Factory(
        CreateDiagramUseCase,
        diagram_service=diagram_service,
        event_bus=providers.Singleton(EventBus)
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
from typing import Protocol, Dict, Type

class NodeHandler(Protocol):
    node_type: str
    
    async def execute(self, context: ExecutionContext, config: Dict) -> NodeResult:
        ...

class HandlerRegistry:
    def __init__(self):
        self._handlers: Dict[str, Type[NodeHandler]] = {}
    
    def register(self, handler_class: Type[NodeHandler]):
        self._handlers[handler_class.node_type] = handler_class
    
    def get_handler(self, node_type: str) -> NodeHandler:
        return self._handlers[node_type]()

# Auto-registration through decorators
def node_handler(node_type: str):
    def decorator(cls):
        cls.node_type = node_type
        handler_registry.register(cls)
        return cls
    return decorator

# Usage
@node_handler("llm")
class LLMNodeHandler:
    async def execute(self, context: ExecutionContext, config: Dict) -> NodeResult:
        # Implementation
```

## Code Generation Strategy

### Single Source of Truth
TypeScript models in `packages/domain-models/` generate:
1. Python domain models (Pydantic)
2. GraphQL schema (SDL)
3. TypeScript types for frontend
4. Python DTOs for application layer
5. CLI operation types

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
│   └── infrastructure/
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

## Migration Strategy

### Phase 1: Foundation (Week 1-2)
1. Set up new package structure
2. Implement DI container
3. Create protocol definitions
4. Set up code generation pipeline

### Phase 2: Domain Extraction (Week 3-4)
1. Extract pure domain models
2. Move domain services
3. Define all ports
4. Create domain events

### Phase 3: Infrastructure Adapters (Week 5-6)
1. Move LLM integrations
2. Move Notion adapter
3. Implement storage adapters
4. Create event bus

### Phase 4: Application Layer (Week 7-8)
1. Extract use cases from handlers
2. Implement orchestration services
3. Create DTOs
4. Wire up DI container

### Phase 5: API Layer Cleanup (Week 9-10)
1. Thin out GraphQL resolvers
2. Remove business logic from API
3. Implement proper error handling
4. Add comprehensive logging

### Phase 6: Testing & Documentation (Week 11-12)
1. Achieve 80% test coverage
2. Document all public APIs
3. Create architecture decision records
4. Update developer guides

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

## Deployment Architecture

### Container Strategy
```dockerfile
# Base image for all Python packages
FROM python:3.11-slim as base

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