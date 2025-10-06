# Domain Layer

Pure business logic following DDD and hexagonal architecture.

## Principles
- **No dependencies** on infrastructure/application layers
- **Port interfaces** (protocols) for infrastructure to implement
- **Rich domain models** with behavior, not just data

## Bounded Contexts

### 1. Conversation (`conversation/`)
- **Person**: Agent with memory selection and execution capabilities
- **IntelligentMemoryStrategy**: LLM-based memory selection with scoring and deduplication
  - MemoryConfig: Configuration for memory selection behavior
  - MessageScorer: Scores messages by recency, frequency, relevance
  - MessageDeduplicator: Removes duplicate messages based on content overlap
- **Conversation**: Dialogue history management
- **Ports**: LLMService protocol for memory selection

### 2. Diagram (`diagram/`)
- **Compilation**: DomainCompiler, NodeFactory, ConnectionResolver, CompileTimeResolver
- **Strategies**: Native, Readable, Light, Executable formats
- **Models**: ExecutableDiagram, ExecutableNode/Edge
- **Services**: DiagramFormatDetector, DiagramStatisticsService
- **Validation**: DiagramValidator and validation rules
- **Utils**: Helper utilities for diagram processing

### 3. Claude Code Translation (`cc_translate/`)
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
- **Resolution**: RuntimeInputResolver, TransformationEngine, NodeStrategies
- **State Management**: StateTracker, ExecutionTracker
- **Token Management**: TokenManager, TokenTypes
- **Rules**: ConnectionRules, TransformRules
- **Context**: ExecutionContext management
- **Envelope**: EnvelopeFactory for unified output pattern

### 5. Codegen (`codegen/`)
- **IR Models**: Intermediate representation models for code generation
- **IR Builder Port**: Port interface for IR builders
- **Ports**: External service interfaces for code generation

### 6. Events (`events/`)
- Event contracts and messaging patterns
- Unified EventBus protocol

### 7. Integrations (`integrations/`)
- **API Services** (`api_services/`): APIBusinessLogic, retry policies
- **API Value Objects** (`api_value_objects/`): API-related value objects
- **DB Services** (`db_services/`): Database domain services
- **File Value Objects** (`file_value_objects/`): File-related value objects
- **Validators**: API, Data, File, Notion validation logic
- **Ports**: Integration service interfaces

### 8. Base (`base/`)
- BaseValidator, exceptions, service base classes

## Key Patterns

```python
# Value Objects - Immutable, self-validating
@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay: float = 1.0

# Domain Services - Stateless business logic
class DiagramStatisticsService:
    def calculate_complexity(self, diagram: DomainDiagram) -> ComplexityMetrics:
        pass

# Memory Strategy - Intelligent memory selection
class IntelligentMemoryStrategy:
    def __init__(self, llm_service: LLMServicePort, config: Optional[MemoryConfig] = None):
        self._llm_service = llm_service
        self._config = config or MemoryConfig()
        self._scorer = MessageScorer(self._config)
        self._deduplicator = MessageDeduplicator(self._config)

    async def select_memories(self, person_id, messages, criteria, at_most):
        # LLM-based intelligent memory selection with scoring and deduplication

# Strategies - Pluggable algorithms
class BaseConversionStrategy(FormatStrategy, ABC):
    @abstractmethod
    def extract_nodes(self, data: dict) -> list[dict]:
        pass

# Validators - Rules with warnings/errors
class DiagramValidator(BaseValidator):
    def _perform_validation(self, diagram, result):
        pass

# Ports - Domain interfaces
class LLMServicePort(Protocol):
    async def select_memories(
        self, person_id: PersonID, candidate_messages: Sequence[Message],
        task_preview: str, criteria: str, at_most: Optional[int]
    ) -> list[str]:
        ...
```


## Usage Guidelines

### Adding Business Logic
1. Choose: value object, entity, or service
2. Place in appropriate bounded context
3. Write pure unit tests
4. Define ports for I/O

### Module Organization for Large Services
When a domain service grows beyond ~400 lines, consider refactoring into a module:
```
domain/context/service_module/
├── __init__.py         # Export main service class
├── service.py          # Main orchestration logic (~150-200 lines)
├── builders.py         # Factory/builder methods
├── utils.py            # Utility functions
└── specialized.py      # Specialized logic
```
Example: `cc_translate/` module for Claude Code translation

### Extending Validators
```python
class MyValidator(BaseValidator):
    def _perform_validation(self, target, result):
        if not self._check_rule(target):
            result.add_error(ValidationError("Rule violated"))
```

### Adding Diagram Formats
1. Extend `BaseConversionStrategy`
2. Register in `DiagramFormatDetector`
3. Implement node/arrow extraction


## Testing

- **Unit tests only** - pure functions, no I/O
- **No mocks** - in-memory operations
- **Fast** - milliseconds per test

```python
def test_connection_rules():
    assert NodeConnectionRules.can_connect(NodeType.START, NodeType.PERSON_JOB)
    assert not NodeConnectionRules.can_connect(NodeType.ENDPOINT, NodeType.START)
```

## Import Paths

```python
# Current imports (v2.0 refactored)
from dipeo.domain.diagram.compilation import CompileTimeResolver, Connection, TransformRules
from dipeo.domain.cc_translate.phase_coordinator import PhaseCoordinator  # Claude Code session orchestration
from dipeo.domain.cc_translate.convert.converter import Converter
from dipeo.domain.execution.resolution import RuntimeInputResolver, TransformationEngine
from dipeo.domain.execution.envelope import EnvelopeFactory  # Unified output pattern
from dipeo.application.execution.events import EventPipeline  # Use EventPipeline for event management
from dipeo.domain.execution.state_tracker import StateTracker
from dipeo.domain.execution.token_manager import TokenManager
from dipeo.domain.events import EventBus  # Unified event protocol
from dipeo.domain.integrations.ports import LLMService as LLMServicePort
from dipeo.domain.integrations.api_services import APIBusinessLogic
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.memory_strategies import IntelligentMemoryStrategy, MemoryConfig
from dipeo.domain.conversation.ports import LLMService
from dipeo.domain.codegen.ir_models import IRSchema, IRTypeDefinition
from dipeo.domain.codegen.ir_builder_port import IRBuilderPort
```

## Envelope Pattern Usage

The unified envelope pattern uses `EnvelopeFactory.create()` for all envelope creation:

```python
from dipeo.domain.execution.envelope import EnvelopeFactory
from dipeo.diagram_generated.enums import ContentType  # For explicit content types

# Basic envelope creation (auto-detects content type)
envelope = EnvelopeFactory.create("Hello world")  # Creates RAW_TEXT
envelope = EnvelopeFactory.create({"key": "value"})  # Creates OBJECT
envelope = EnvelopeFactory.create(b"binary data")  # Creates BINARY

# Explicit content type specification
envelope = EnvelopeFactory.create(
    body="some text",
    content_type=ContentType.RAW_TEXT,
    produced_by="my_node"
)

# Error envelopes
envelope = EnvelopeFactory.create(
    body="Something went wrong", 
    error="ValidationError",
    produced_by="validator_node"
)

# With additional metadata
envelope = EnvelopeFactory.create(
    body={"result": "success"},
    meta={"timestamp": time.time(), "custom_field": "value"}
)
```

## Dependencies

- Python standard library
- `dipeo.models` - Generated domain models
- **No framework dependencies** (no FastAPI, SQLAlchemy, etc.)
