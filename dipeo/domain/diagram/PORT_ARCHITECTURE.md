# Port Architecture Design Decisions

## Overview

This document explains the architectural decisions behind DiPeO's port interfaces, focusing on Single Responsibility Principle (SRP) and clear separation of concerns.

## Port Interface Responsibilities

### DiagramStorageSerializer (ports.py)

**Responsibility**: Serialize/deserialize diagrams to/from storage formats

**Interface**:
```python
class DiagramStorageSerializer(ABC):
    @abstractmethod
    def serialize_for_storage(self, diagram: DomainDiagram, format: str) -> str: ...

    @abstractmethod
    def deserialize_from_storage(
        self, content: str, format: str | None = None, diagram_path: str | None = None
    ) -> DomainDiagram: ...
```

**Design Decision**: This port is ONLY for storage serialization. It does NOT include validation.

**Rationale**:
- **SRP**: Serializers should serialize, validators should validate
- **Separation of concerns**: Validation logic lives in `dipeo/domain/diagram/validation/`
- **Single source of truth**: The domain compiler is the authoritative source for all validation
- **Avoid duplication**: Having validate() here would duplicate validation logic

**Historical Note**: Previously, this port included a `validate()` method that would attempt deserialization and return success/failure. This was removed because:
1. It was dead code (never called in production)
2. It violated SRP (mixed serialization with validation concerns)
3. It created confusion about where validation should happen

### FormatStrategy (ports.py)

**Responsibility**: Handle format-specific parsing, serialization, and detection

**Interface**:
```python
class FormatStrategy(ABC):
    @abstractmethod
    def parse(self, content: str) -> Any: ...

    @abstractmethod
    def format(self, data: Any) -> str: ...

    @abstractmethod
    def deserialize_to_domain(self, content: str, diagram_path: str | None = None) -> DomainDiagram: ...

    @abstractmethod
    def serialize_from_domain(self, diagram: DomainDiagram) -> str: ...

    @abstractmethod
    def detect_confidence(self, data: dict[str, Any]) -> float: ...

    @property
    @abstractmethod
    def format_id(self) -> str: ...

    @property
    @abstractmethod
    def format_info(self) -> dict[str, str]: ...

    def quick_match(self, content: str) -> bool: ...
```

**Design Decision**: Includes `quick_match()` helper method

**Rationale**:
- **Direct responsibility**: Format detection is part of format strategy's core job
- **Convenience**: Simple heuristic for quick format identification
- **No violation**: This is not validation; it's format detection

### Segregated Ports (segregated_ports.py)

Following Interface Segregation Principle, we split the monolithic DiagramPort into focused interfaces:

#### DiagramFilePort

**Responsibility**: File I/O operations

```python
class DiagramFilePort(Protocol):
    async def load_from_file(self, file_path: str) -> DomainDiagram: ...
    async def save_to_file(self, diagram: DomainDiagram, file_path: str, format_type: str = "native") -> None: ...
    async def file_exists(self, file_path: str) -> bool: ...
    async def delete_file(self, file_path: str) -> None: ...
```

**SRP Compliance**: Only file system operations

#### DiagramFormatPort

**Responsibility**: Format detection and conversion

```python
class DiagramFormatPort(Protocol):
    def detect_format(self, content: str) -> DiagramFormat: ...
    def serialize(self, diagram: DomainDiagram, format_type: str) -> str: ...
    def deserialize(self, content: str, format_type: str | None = None, diagram_path: str | None = None) -> DomainDiagram: ...
    def convert_format(self, diagram: DomainDiagram, from_format: str, to_format: str) -> str: ...
```

**SRP Compliance**: Only format-related operations

#### DiagramRepositoryPort

**Responsibility**: CRUD and query operations

```python
class DiagramRepositoryPort(Protocol):
    async def create(self, name: str, diagram: DomainDiagram, format_type: str = "native") -> str: ...
    async def get(self, diagram_id: str) -> Optional[DomainDiagram]: ...
    async def update(self, diagram_id: str, diagram: DomainDiagram) -> None: ...
    async def delete(self, diagram_id: str) -> None: ...
    async def exists(self, diagram_id: str) -> bool: ...
    async def list(self, format_type: str | None = None) -> list[DiagramInfo]: ...
```

**SRP Compliance**: Only persistence operations

#### DiagramCompiler

**Responsibility**: Compile DomainDiagram to ExecutableDiagram

```python
class DiagramCompiler(Protocol):
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram: ...
```

**SRP Compliance**: Single method, single responsibility

## Validation Architecture

**Location**: `dipeo/domain/diagram/validation/`

**Design**: Validation is a separate concern with its own module

**Key Principle**: The domain compiler is the single source of truth for validation

**Interfaces**:
```python
# High-level façade
class DiagramValidator(BaseValidator):
    def validate(self, diagram: DomainDiagram) -> ValidationResult: ...

# Direct validation functions
def validate_diagram(diagram: DomainDiagram) -> CompilationResult: ...
def validate_structure_only(diagram: DomainDiagram) -> CompilationResult: ...
def validate_connections(diagram: DomainDiagram) -> CompilationResult: ...
```

**Why separate?**
1. **SRP**: Validation is fundamentally different from serialization or storage
2. **Complexity**: Validation involves business rules, structural checks, and compilation phases
3. **Reusability**: Validation logic can be used independently of storage/serialization
4. **Testing**: Easier to test validation in isolation

## When to Add Validation to a Port?

**Answer**: Almost never.

**Exception**: Only if validation is an intrinsic part of the port's core responsibility. For example:
- ✅ Format detection (part of format strategy's job)
- ❌ Diagram validation (should be in validation module)
- ❌ Content validation (should use validation module)
- ❌ Business rule validation (should be in domain services)

## Anti-Patterns to Avoid

### ❌ Mixing Serialization with Validation

```python
# BAD: Validation in serializer
class DiagramStorageSerializer(ABC):
    def validate(self, content: str) -> tuple[bool, list[str]]:
        # This violates SRP
        ...
```

**Why bad?**
- Serializers should serialize
- Creates confusion about where validation lives
- Duplicates validation logic
- Breaks single source of truth principle

### ❌ Convenience Methods That Blur Responsibilities

```python
# BAD: Repository doing validation
class DiagramRepositoryPort(Protocol):
    async def validate_and_save(self, diagram: DomainDiagram) -> bool:
        # This combines two concerns
        ...
```

**Why bad?**
- Repositories should persist
- Forces validation logic into wrong layer
- Makes testing harder
- Couples persistence with validation

## Best Practices

### ✅ Keep Ports Focused

Each port should have ONE clear responsibility:
- Storage → File I/O
- Serialization → Format conversion
- Validation → Business rules and structural checks
- Compilation → Transform domain to executable

### ✅ Use Composition, Not Kitchen Sink Ports

Instead of one giant port with many methods, create multiple focused ports:

```python
# GOOD: Focused ports composed together
class DiagramService:
    def __init__(
        self,
        file_port: DiagramFilePort,
        format_port: DiagramFormatPort,
        validator: DiagramValidator,
        compiler: DiagramCompiler,
    ):
        ...
```

### ✅ Delegate Cross-Cutting Concerns

Don't add methods like `validate()`, `log()`, `cache()` to domain ports. Instead:
- Validation → Use `DiagramValidator`
- Logging → Use infrastructure decorators
- Caching → Use infrastructure decorators
- Error handling → Use application layer

## Summary

DiPeO's port architecture strictly follows Single Responsibility Principle:

1. **Each port has ONE clear responsibility**
2. **Validation is always separate** (in validation module)
3. **Serialization does NOT include validation**
4. **Ports are composed, not combined**
5. **Cross-cutting concerns use decorators/middleware**

This design makes the codebase:
- Easier to understand (clear boundaries)
- Easier to test (focused interfaces)
- Easier to extend (add new ports without changing existing ones)
- More maintainable (changes are localized)

## References

- Validation architecture: `dipeo/domain/diagram/validation/README.md`
- Port implementations: `dipeo/infrastructure/diagram/adapters/`
- Use cases: `dipeo/application/diagram/use_cases/`
