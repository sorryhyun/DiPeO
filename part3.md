# DiPeO Refactoring Plan - Part 3: Comprehensive Analysis and Implementation Strategy

## Executive Summary

This plan addresses the architectural debt in DiPeO by applying hexagonal architecture principles, consolidating redundant implementations, and establishing clear boundaries between layers. The refactoring will reduce the codebase by ~30%, improve type safety, and establish a foundation for scalable growth.

## Current State Analysis

### Major Issues Identified

1. **Service Registry Fragmentation** ✅ RESOLVED
   - `dipeo/domain/service_registry.py` - Added deprecation warnings
   - `dipeo/application/unified_service_registry.py` - Migrating to new registry
   - Container system updated to use new unified registry

2. **File Service Complexity** ✅ RESOLVED
   - Created port definitions in `dipeo/domain/ports/storage.py`
   - Implemented 3 capability-based adapters (S3, LocalBlob, LocalFileSystem)
   - Created ArtifactStore for high-level artifact management
   - Migration guide and examples provided

3. **Validation Sprawl**
   - `dipeo/core/base/validator.py` - Abstract base
   - `dipeo/domain/validators/` - 7 validators with similar patterns
   - `dipeo/diagram_generated/validation/` - Generated validators
   - Validation happening at wrong layers (inside domain logic)

4. **Compilation Pipeline Duplication**
   - `dipeo/application/resolution/` - Main compilation
   - `dipeo/application/execution/resolution/` - Input resolution
   - `dipeo/core/static/diagram_compiler.py` - Another compiler
   - Three separate pipelines doing similar work

5. **Container Over-engineering**
   - 6 containers across core/ and runtime/
   - Complex initialization with profiles
   - Circular dependency risks

6. **Service Layer Confusion**
   - Services scattered across 6+ directories
   - No clear boundary between domain/application/infrastructure services
   - Mixed responsibilities

## Target Architecture

### Layer Structure
```
dipeo/
├── domain/              # Pure business logic, protocols only
│   ├── models/          # Domain entities, value objects
│   ├── ports/           # Protocol definitions (interfaces)
│   └── services/        # Domain services (pure logic)
├── application/         # Use cases and orchestration
│   ├── services/        # Application services
│   ├── registry/        # Single service registry
│   └── compilation/     # Unified compilation pipeline
├── infrastructure/      # External integrations
│   ├── adapters/        # Port implementations
│   └── persistence/     # Storage implementations
└── diagram_generated/   # Generated DTOs and adapters only
```

## Detailed Refactoring Plan

### ✅ Phase 1: Registry Consolidation (COMPLETED)

Registry consolidation has been successfully implemented:
- Created type-safe `ServiceRegistry` with `ServiceKey` pattern in `dipeo/application/registry/`
- Defined all service keys in `keys.py` with proper type hints
- Implemented `MigrationServiceRegistry` adapter for backward compatibility
- Added deprecation warnings to old domain registry
- Updated containers to use new registry system
- Tested and verified functionality with `dipeo run`

### ✅ Phase 2: Port Definition and File Service Consolidation (COMPLETED)

File service consolidation has been successfully implemented:
- Created clean port definitions in `dipeo/domain/ports/storage.py`:
  - `BlobStorePort` for object storage with versioning
  - `FileSystemPort` for POSIX-like file operations
  - `ArtifactStorePort` for high-level artifact management
- Implemented adapters in `dipeo/infrastructure/adapters/storage/`:
  - `S3Adapter` for cloud storage
  - `LocalBlobAdapter` and `LocalFileSystemAdapter` for local storage
  - `ArtifactStoreAdapter` for artifact versioning and promotion
- Added `StorageError` to core exceptions
- Created comprehensive migration guide and examples

### Phase 3: Validation Framework (Next Priority)

#### 3.1 Boundary-Only Validation

```python
# dipeo/infrastructure/adapters/api/diagram_adapter.py
from pydantic import BaseModel, ValidationError
from dipeo.domain.models import Diagram

class DiagramDTO(BaseModel):
    """DTO for API boundary"""
    id: str
    name: str
    nodes: list[dict]
    edges: list[dict]

class DiagramAPIAdapter:
    """Validates at API boundary only"""
    def from_request(self, data: dict) -> Diagram:
        # Validate untrusted input
        try:
            dto = DiagramDTO(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid diagram data: {e}")
        
        # Convert to domain model (no validation needed)
        return Diagram(
            id=DiagramId(dto.id),
            name=dto.name,
            nodes=[self._to_domain_node(n) for n in dto.nodes],
            edges=[self._to_domain_edge(e) for e in dto.edges]
        )
```

#### 3.2 Domain Invariants (No Framework)

```python
# dipeo/domain/models/diagram.py
from dataclasses import dataclass
from typing import NewType

NodeId = NewType("NodeId", str)

@dataclass(frozen=True, slots=True)
class Node:
    """Domain model with invariants"""
    id: NodeId
    type: str
    config: dict
    
    def __post_init__(self):
        # Simple invariant checks, no framework
        if not self.id:
            raise ValueError("Node ID cannot be empty")
        if not self.type:
            raise ValueError("Node type is required")

@dataclass(frozen=True, slots=True)
class Diagram:
    """Immutable domain model"""
    id: DiagramId
    name: str
    nodes: list[Node]
    edges: list[Edge]
    
    def __post_init__(self):
        # Ensure graph is valid
        node_ids = {n.id for n in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids or edge.target not in node_ids:
                raise ValueError(f"Edge references unknown node")
```

#### 3.3 Remove Validator Classes
1. Delete `dipeo/core/base/validator.py`
2. Remove all classes in `dipeo/domain/validators/`
3. Move validation logic to adapters at boundaries
4. Use Pydantic only for DTOs at I/O boundaries

### Phase 4: Compilation Pipeline Unification

#### 4.1 Single Pass Manager

```python
# dipeo/application/compilation/pass_manager.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol

@dataclass
class CompilationContext:
    """Mutable context passed through compilation passes"""
    input_data: dict
    diagram: Diagram | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def has_errors(self) -> bool:
        return bool(self.errors)

class CompilationPass(ABC):
    """Base class for compilation passes"""
    @abstractmethod
    def run(self, context: CompilationContext) -> CompilationContext:
        """Execute pass and return modified context"""
        ...

class ParsePass(CompilationPass):
    """Parse raw input into initial structure"""
    def run(self, context: CompilationContext) -> CompilationContext:
        try:
            # Parse based on format
            if context.metadata.get("format") == "yaml":
                parsed = yaml.safe_load(context.input_data)
            else:
                parsed = json.loads(context.input_data)
            context.metadata["parsed"] = parsed
        except Exception as e:
            context.errors.append(f"Parse error: {e}")
        return context

@dataclass
class PassManager:
    """Manages compilation pipeline"""
    passes: list[CompilationPass] = field(default_factory=list)
    
    def compile(self, input_data: dict, metadata: dict | None = None) -> ExecutableDiagram:
        """Run all passes in sequence"""
        context = CompilationContext(
            input_data=input_data,
            metadata=metadata or {}
        )
        
        for pass_ in self.passes:
            context = pass_.run(context)
            if context.has_errors():
                raise CompilationError(context.errors)
        
        return context.diagram
```

#### 4.2 Consolidation Steps
1. Move all compilation logic to `dipeo/application/compilation/`
2. Delete `dipeo/core/static/diagram_compiler.py`
3. Merge `dipeo/application/execution/resolution/` into compilation pipeline
4. Create migration shims for old APIs

### Phase 5: Container Simplification

#### 5.1 Three Core Containers

```python
# dipeo/container/containers.py
from dipeo.application.registry import ServiceRegistry, LLM_SERVICE, BLOB_STORE

class CoreContainer:
    """Immutable core services"""
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._setup_domain_services()
    
    def _setup_domain_services(self):
        # Register pure domain services
        self.registry.register(
            DIAGRAM_VALIDATOR,
            DiagramValidationService()
        )

class InfrastructureContainer:
    """External integration adapters"""
    def __init__(self, registry: ServiceRegistry, config: Config):
        self.registry = registry
        self.config = config
        self._setup_adapters()
    
    def _setup_adapters(self):
        # Register infrastructure adapters
        if self.config.storage.type == "s3":
            self.registry.register(
                BLOB_STORE,
                S3Adapter(bucket=self.config.storage.bucket)
            )
        else:
            self.registry.register(
                BLOB_STORE,
                LocalBlobAdapter(path=self.config.storage.path)
            )

class ApplicationContainer:
    """Application services and use cases"""
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._setup_application_services()
    
    def _setup_application_services(self):
        # Register application services with dependencies
        self.registry.register(
            EXECUTION_SERVICE,
            lambda: ExecutionService(
                llm=self.registry.resolve(LLM_SERVICE),
                storage=self.registry.resolve(BLOB_STORE),
            )
        )
```

### Phase 6: Code Generation Boundaries

#### 6.1 Clear Extension Points

```python
# dipeo/domain/ports/node_handler.py
from typing import Protocol

class NodeHandlerPort(Protocol):
    """Extension point for generated nodes"""
    async def handle(self, node_data: dict, context: ExecutionContext) -> NodeOutput:
        """Handle node execution"""
        ...

# dipeo/application/handlers/person_job_handler.py
from dipeo.diagram_generated.dtos import PersonJobDTO

class PersonJobHandler:
    """Handwritten business logic"""
    def __init__(self, llm_service: LLMServicePort):
        self.llm_service = llm_service
    
    async def handle(self, dto: PersonJobDTO, context: ExecutionContext) -> NodeOutput:
        # All business logic here
        person = context.get_person(dto.person_id)
        prompt = self._build_prompt(dto.prompt, person)
        response = await self.llm_service.complete(prompt, temperature=dto.temperature)
        return NodeOutput(success=True, data=response)
```

## Implementation Timeline

### Completed
- ✅ Day 1-2: Registry and Ports
- ✅ Day 3-4: File Services

### Remaining Work
- Day 5-6: Validation Cleanup
  - [ ] Move validation to API boundaries only
  - [ ] Delete all validator classes
  - [ ] Remove validation from domain layer

- Day 7-8: Compilation Pipeline
  - [ ] Build single pass manager
  - [ ] Migrate all formats to use it
  - [ ] Delete 3 old compilation pipelines

- Day 9-10: Container Simplification
  - [ ] Create 3 new containers
  - [ ] Update bootstrap process
  - [ ] Delete 6 old containers

## Expected Outcomes

### Before → After
- **15+ scattered services** → **8 focused services**
- **6 file service implementations** → **3 capability-based adapters** ✅
- **3 compilation pipelines** → **1 pass manager**
- **6 containers** → **3 containers**
- **Domain has registry** → **Only application has registry** ✅
- **Validation everywhere** → **Validation only at boundaries**

### Performance Improvements
- Faster startup (fewer services to initialize)
- Less memory usage (no duplicate services)
- Cleaner execution traces (no validation overhead)

## Next Steps

1. **Phase 3: Validation Framework** - Move all validation to boundaries
2. **Phase 4: Compilation Pipeline** - Unify into single pass manager
3. **Phase 5: Container Simplification** - Reduce to 3 focused containers
4. **Phase 6: Code Generation Boundaries** - Clear separation of generated vs handwritten code

## Migration Notes

For file services, use the migration guide at `dipeo/infrastructure/adapters/storage/MIGRATION_GUIDE.md` which includes:
- Before/after code examples
- Service registration patterns
- Testing strategies
- Gradual migration approaches