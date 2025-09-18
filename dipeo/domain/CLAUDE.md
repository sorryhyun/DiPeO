# Domain Layer

Pure business logic following DDD and hexagonal architecture.

## Principles
- **No dependencies** on infrastructure/application layers
- **Port interfaces** (protocols) for infrastructure to implement
- **Rich domain models** with behavior, not just data

## Bounded Contexts

### 1. Conversation (`conversation/`)
- **Person**: Agent with Brain (memory selection) and Hand (execution) components
- **CognitiveBrain**: Memory selection, scoring, and deduplication logic
  - MessageScorer: Scores messages by recency, frequency, relevance
  - MessageDeduplicator: Removes duplicate messages based on content overlap
  - MemorySelectionConfig: Configuration for memory selection behavior
- **Conversation**: Dialogue history management
- **Ports**: MemorySelectionPort protocol for LLM-based selection

### 2. Diagram (`diagram/`)
- **Compilation**: DomainCompiler, NodeFactory, ConnectionResolver, CompileTimeResolver
- **Strategies**: Native, Readable, Light, Executable formats
- **Models**: ExecutableDiagram, ExecutableNode/Edge
- **Claude Code Translation** (`cc_translate/`): Converts Claude Code sessions to DiPeO diagrams
  - `translator.py`: Main orchestration logic
  - `node_builders.py`: Node creation for different tool types
  - `text_utils.py`: Text extraction and unescaping
  - `diff_utils.py`: Unified diff generation for Edit operations
- **Services**: DiagramFormatDetector, DiagramStatisticsService

### 3. Execution (`execution/`)
- **Resolution**: RuntimeInputResolver, TransformationEngine, NodeStrategies
- ConnectionRules, TransformRules  
- DynamicOrderCalculator

### 4. Events (`events/`)
- Event contracts and messaging patterns

### 5. Integrations (`integrations/`)
- **API**: APIBusinessLogic, RetryPolicy
- **Database**: DBOperationsDomainService
- **File**: FileExtension, FileSize, Checksum
- **Validators**: API, Data, File, Notion

### 6. Base (`base/`)
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

# Cognitive Components - Memory and reasoning
class CognitiveBrain:
    def __init__(self, memory_selector: MemorySelectionPort):
        self._memory_selector = memory_selector
        self._scorer = MessageScorer()
        self._deduplicator = MessageDeduplicator()
    
    async def select_memories(self, messages, criteria, at_most):
        # Intelligent memory selection with scoring and filtering

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
class MemorySelectionPort(Protocol):
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
# Current imports (v1.0 unified)
from dipeo.domain.diagram.compilation import CompileTimeResolver, Connection, TransformRules
from dipeo.domain.diagram.cc_translate import ClaudeCodeTranslator  # Claude Code session translation
from dipeo.domain.execution.resolution import RuntimeInputResolver, TransformationEngine
from dipeo.domain.execution.envelope import EnvelopeFactory  # Unified output pattern
from dipeo.domain.events import EventBus  # Unified event protocol
from dipeo.domain.ports.storage import StoragePort
from dipeo.domain.integrations.api_services import APIBusinessLogic
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.brain import CognitiveBrain, MemorySelectionConfig
from dipeo.domain.conversation.ports import MemorySelectionPort
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

### Deprecated Methods (v1.0)

The following methods are deprecated and will be removed. Use `EnvelopeFactory.create()` instead:

```python
# DEPRECATED - Use EnvelopeFactory.create() instead
EnvelopeFactory.text("content")           # → EnvelopeFactory.create("content")
EnvelopeFactory.json(data)               # → EnvelopeFactory.create(data)
EnvelopeFactory.binary(bytes_data)       # → EnvelopeFactory.create(bytes_data)
EnvelopeFactory.error("msg", "ErrorType") # → EnvelopeFactory.create("msg", error="ErrorType")
EnvelopeFactory.conversation(state)     # → EnvelopeFactory.create(state, content_type=ContentType.CONVERSATION_STATE)
```

## v1.0 Domain Changes (2025-09-05)

### Unified Patterns
- **EventBus Protocol**: Single unified interface for all event handling (replaces DomainEventBus, EventEmitter, etc.)
- **Envelope Pattern**: Complete migration from NodeOutput to Envelope for all handler outputs
  - New `EnvelopeFactory.create()` method with auto-detection and unified interface
  - Deprecated specific factory methods (`text()`, `json()`, `error()`, etc.)
  - Consistent error handling through the `error` parameter
- **Protocol Consistency**: Direct protocol implementation without unnecessary adapter layers

### Naming Conventions
- **Python Internal**: snake_case for all generated Python code
- **JSON/GraphQL Compatibility**: Pydantic Field(alias=...) provides camelCase for external APIs
- **Type Safety**: Maintained across all transformations

## Dependencies

- Python standard library
- `dipeo.models` - Generated domain models
- **No framework dependencies** (no FastAPI, SQLAlchemy, etc.)
