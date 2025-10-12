# Domain Layer Architecture

Pure business logic following Domain-Driven Design (DDD) and hexagonal architecture principles.

## Core Principles

- **No dependencies** on infrastructure/application layers
- **Port interfaces** (protocols) for infrastructure to implement
- **Rich domain models** with behavior, not just data
- **Pure business logic** - All domain code should be testable without I/O

## Bounded Contexts

The domain is organized into 9 bounded contexts, each representing a cohesive area of business logic:

### 1. Conversation (`conversation/`)
**Purpose**: Agent conversation and memory management

**Core Concepts**:
- **Person**: Agent with memory selection and execution capabilities
- **IntelligentMemoryStrategy**: LLM-based memory selection with scoring and deduplication
  - MemoryConfig: Configuration for memory selection behavior
  - MessageScorer: Scores messages by recency, frequency, relevance
  - MessageDeduplicator: Removes duplicate messages based on content overlap
- **Conversation**: Dialogue history management
- **Ports**: LLMService protocol for memory selection

### 2. Diagram (`diagram/`)
**Purpose**: Diagram compilation and format conversion

**Core Concepts**:
- **Compilation Pipeline** (`compilation/`):
  - DomainDiagramCompiler: Multi-phase compilation orchestrator
  - Phases: 6-phase pipeline (Validation → Transformation → Resolution → Edge Building → Optimization → Assembly)
  - Types: CompilationResult, CompilationContext, CompilationPhase enum
  - Helpers: NodeFactory, ConnectionResolver, EdgeBuilder
- **Format Strategies** (`strategies/`):
  - Consistent pattern: parser → transformer → serializer → strategy
  - Light format: YAML/JSON with simplified syntax
  - Readable format: Markdown-based diagrams
  - Each strategy provides bidirectional conversion to/from DomainDiagram
- **Configuration-Driven Components** (`utils/`):
  - HandleSpec: Declarative handle configuration (HANDLE_SPECS table)
  - NodeFieldMapper: Table-driven field mappings (FIELD_MAPPINGS)
  - DiagramDataExtractor: Unified data extraction
  - PersonReferenceResolver: Person label ↔ ID resolution
  - HandleIdOperations: Handle ID parsing and creation
  - ArrowBuilder, NodeBuilder: Component builders
- **Models**: ExecutableDiagram, ExecutableNode/Edge, format-specific models
- **Services**: DiagramFormatDetector, DiagramStatisticsService
- **Validation**: DiagramValidator with phase-based error reporting

### 3. Claude Code Translation (`cc_translate/`)
**Purpose**: Converting Claude Code sessions into DiPeO diagrams

**Core Concepts**:
- **PhaseCoordinator**: Main orchestration for session conversion
- **Convert Module**:
  - `converter.py`: Core conversion logic
  - `node_builder_refactored.py`: Node creation for different tool types
  - `diagram_assembler.py`: Diagram assembly and structuring
  - `connection_builder.py`: Connection logic between nodes
  - `person_registry.py`: Registry for person nodes
  - `node_factories/`: Specialized node factory implementations
- **Preprocess**: Input preprocessing and validation
- **Post-processing**: Session optimization and pruning
- **Models**: Domain models for Claude Code translation
- **Ports**: External service interfaces

### 4. Execution (`execution/`)
**Purpose**: Runtime execution and state management

**Core Concepts**:
- **Resolution**: RuntimeInputResolver, TransformationEngine, NodeStrategies
- **State Management**: StateTracker, ExecutionTracker
- **Token Management**: TokenManager, TokenTypes
- **Rules**: ConnectionRules, TransformRules
- **Context**: ExecutionContext management
- **Envelope**: EnvelopeFactory for unified output pattern

### 5. Codegen (`codegen/`)
**Purpose**: Code generation domain models

**Core Concepts**:
- **IR Models**: Intermediate representation models for code generation
- **IR Builder Port**: Port interface for IR builders
- **Ports**: External service interfaces for code generation

### 6. Events (`events/`)
**Purpose**: Event contracts and messaging

**Core Concepts**:
- Event contracts and messaging patterns
- Unified EventBus protocol

### 7. Integrations (`integrations/`)
**Purpose**: External service integration logic

**Core Concepts**:
- **API Services** (`api_services/`): APIBusinessLogic, retry policies
- **API Value Objects** (`api_value_objects/`): API-related value objects
- **DB Services** (`db_services/`): Database domain services
- **File Value Objects** (`file_value_objects/`): File-related value objects
- **Validators**: API, Data, File, Notion validation logic
- **Ports**: Integration service interfaces

### 8. Base (`base/`)
**Purpose**: Base classes and shared utilities

**Core Concepts**:
- BaseValidator, exceptions, service base classes

### 9. Ports (`ports/`)
**Purpose**: Infrastructure interface definitions

**Core Concepts**:
- Storage ports, service ports, protocol definitions

## Key Patterns

### Value Objects
Immutable, self-validating data structures:
```python
@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay: float = 1.0
```

### Domain Services
Stateless business logic:
```python
class DiagramStatisticsService:
    def calculate_complexity(self, diagram: DomainDiagram) -> ComplexityMetrics:
        pass
```

### Memory Strategy
Intelligent memory selection:
```python
class IntelligentMemoryStrategy:
    def __init__(self, llm_service: LLMServicePort, config: Optional[MemoryConfig] = None):
        self._llm_service = llm_service
        self._config = config or MemoryConfig()
        self._scorer = MessageScorer(self._config)
        self._deduplicator = MessageDeduplicator(self._config)

    async def select_memories(self, person_id, messages, criteria, at_most):
        # LLM-based intelligent memory selection with scoring and deduplication
```

### Strategies
Pluggable algorithms:
```python
class BaseConversionStrategy(FormatStrategy, ABC):
    @abstractmethod
    def extract_nodes(self, data: dict) -> list[dict]:
        pass
```

### Validators
Rules with warnings/errors:
```python
class DiagramValidator(BaseValidator):
    def _perform_validation(self, diagram, result):
        pass
```

### Ports
Domain interfaces for infrastructure to implement:
```python
class LLMServicePort(Protocol):
    async def select_memories(
        self, person_id: PersonID, candidate_messages: Sequence[Message],
        task_preview: str, criteria: str, at_most: Optional[int]
    ) -> list[str]:
        ...
```

## Module Organization Philosophy

### When to Create a Module
When a domain service grows beyond ~400 lines, consider refactoring into a module structure:

```
domain/context/service_module/
├── __init__.py         # Export main service class
├── service.py          # Main orchestration logic (~150-200 lines)
├── builders.py         # Factory/builder methods
├── utils.py            # Utility functions
└── specialized.py      # Specialized logic
```

**Example**: `cc_translate/` module for Claude Code translation

### Single Responsibility
Each bounded context should have a single, well-defined responsibility and clear boundaries with other contexts.

## Testing Philosophy

- **Unit tests only** - Pure functions, no I/O
- **No mocks** - In-memory operations
- **Fast** - Milliseconds per test

Example:
```python
def test_connection_rules():
    assert NodeConnectionRules.can_connect(NodeType.START, NodeType.PERSON_JOB)
    assert not NodeConnectionRules.can_connect(NodeType.ENDPOINT, NodeType.START)
```

## Dependencies

- Python standard library
- `dipeo.models` - Generated domain models
- **No framework dependencies** (no FastAPI, SQLAlchemy, etc.)

## Boundary Enforcement

The domain layer should:
- Never import from application or infrastructure layers
- Define ports (protocols) for infrastructure concerns
- Contain only pure business logic
- Be fully testable without external dependencies
