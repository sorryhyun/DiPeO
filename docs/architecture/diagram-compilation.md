# Diagram Compilation Architecture

DiPeO's diagram compilation system transforms visual diagrams into executable workflows through a multi-phase compilation pipeline. This architecture provides clean separation of concerns, configuration-driven approaches, and comprehensive error reporting.

## Overview

The compilation system follows a pipeline architecture with six distinct phases:

```
DomainDiagram → [6 Phases] → ExecutableDiagram
              ↓
    Validation → Transformation → Resolution → Edge Building → Optimization → Assembly
```

Each phase is responsible for a specific transformation and can report errors/warnings independently.

## Core Components

### DomainDiagramCompiler

Location: `/dipeo/domain/diagram/compilation/domain_compiler.py`

The main compiler orchestrates the compilation pipeline:

```python
compiler = DomainDiagramCompiler()
executable_diagram = compiler.compile(domain_diagram)  # Raises on error

# Or get detailed diagnostics:
result = compiler.compile_with_diagnostics(domain_diagram)
if result.is_valid:
    diagram = result.diagram
else:
    for error in result.errors:
        print(f"{error.phase.name}: {error.message}")
```

**Key Features:**
- Multi-phase compilation with early exit on errors
- Detailed error reporting with phase, message, and node/arrow context
- Support for partial compilation (stop_after parameter for testing)
- Bidirectional compilation (compile and decompile)

### CompilationContext

Location: `/dipeo/domain/diagram/compilation/phases/base.py`

Context object passed through all phases containing:

**Input:**
- `domain_diagram`: Source DomainDiagram to compile

**Phase Outputs:**
- `nodes_list`: Extracted nodes list
- `arrows_list`: Extracted arrows list
- `typed_nodes`: Typed ExecutableNode instances
- `node_map`: NodeID → ExecutableNode mapping
- `resolved_connections`: Resolved connection data
- `typed_edges`: ExecutableEdgeV2 instances

**Metadata:**
- `start_nodes`: Set of START node IDs
- `person_nodes`: Person ID → node IDs mapping
- `node_dependencies`: Dependency graph for optimization

**Result:**
- `result`: CompilationResult with errors/warnings and final diagram

## Compilation Phases

### Phase 1: Validation Phase

**File:** `/dipeo/domain/diagram/compilation/phases/validation_phase.py`

**Purpose:** Structural and semantic validation

**Operations:**
- Extract nodes and arrows from diagram
- Validate unique node IDs
- Validate node types (NodeType enum)
- Validate presence of START and ENDPOINT nodes
- Validate arrow handle references
- Validate node connection rules (incoming/outgoing counts)
- Validate condition node branches

**Output:** `nodes_list`, `arrows_list`

**Example Errors:**
- "Duplicate node IDs found: ['node_1', 'node_1']"
- "Invalid node type: 'invalid_type' (not a NodeType enum)"
- "Diagram must have at least one start node"

### Phase 2: Node Transformation Phase

**File:** `/dipeo/domain/diagram/compilation/phases/node_transformation_phase.py`

**Purpose:** Convert domain nodes to typed ExecutableNode instances

**Operations:**
- Use NodeFactory to create typed nodes (PersonJobNode, CodeJobNode, etc.)
- Build node_map for fast lookups
- Track START nodes and person_nodes

**Dependencies:**
- NodeFactory (configuration-driven node creation)

**Output:** `typed_nodes`, `node_map`, `start_nodes`, `person_nodes`

### Phase 3: Connection Resolution Phase

**File:** `/dipeo/domain/diagram/compilation/phases/connection_resolution_phase.py`

**Purpose:** Resolve handle references to connection data

**Operations:**
- Use ConnectionResolver to parse arrow handle IDs
- Extract source/target node IDs and handle labels
- Validate handle references exist

**Dependencies:**
- ConnectionResolver (handle parsing and validation)

**Output:** `resolved_connections`

### Phase 4: Edge Building Phase

**File:** `/dipeo/domain/diagram/compilation/phases/edge_building_phase.py`

**Purpose:** Create executable edges with content type rules

**Operations:**
- Use EdgeBuilder to create ExecutableEdgeV2 instances
- Apply content type propagation rules
- Handle conditional branching (condtrue/condfalse)
- Set edge metadata

**Dependencies:**
- EdgeBuilder (edge creation with rules)

**Output:** `typed_edges`

### Phase 5: Optimization Phase

**File:** `/dipeo/domain/diagram/compilation/phases/optimization_phase.py`

**Purpose:** Optimize execution paths and build dependency graph

**Operations:**
- Build execution dependency graph
- Identify parallelizable paths
- Detect cycles (raises error)
- Calculate execution order hints

**Output:** `node_dependencies`

**Example Errors:**
- "Cycle detected in diagram: node_1 → node_2 → node_1"

### Phase 6: Assembly Phase

**File:** `/dipeo/domain/diagram/compilation/phases/assembly_phase.py`

**Purpose:** Create final ExecutableDiagram

**Operations:**
- Assemble all components into ExecutableDiagram
- Set metadata
- Finalize compilation result

**Output:** `result.diagram`

## Supporting Utilities

### Configuration-Driven Handle Generation

**File:** `/dipeo/domain/diagram/utils/shared_components.py`

Instead of if-elif chains, handle generation uses declarative configuration:

```python
@dataclass
class HandleSpec:
    label: HandleLabel
    direction: HandleDirection
    data_type: DataType = DataType.ANY

HANDLE_SPECS: dict[str, list[HandleSpec]] = {
    NodeType.CONDITION.value: [
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.INPUT),
        HandleSpec(HandleLabel.CONDTRUE, HandleDirection.OUTPUT, DataType.BOOLEAN),
        HandleSpec(HandleLabel.CONDFALSE, HandleDirection.OUTPUT, DataType.BOOLEAN),
    ],
    NodeType.PERSON_JOB.value: [
        HandleSpec(HandleLabel.FIRST, HandleDirection.INPUT),
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.INPUT),
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.OUTPUT),
    ],
    # ... more node types
}
```

**Usage:**
```python
handle_generator = HandleGenerator()
handle_generator.generate_for_node(diagram, node_id, node_type)
```

### Table-Driven Field Mapping

**File:** `/dipeo/domain/diagram/utils/node_field_mapper.py`

Field mappings between formats use declarative tables:

```python
FIELD_MAPPINGS: dict[str, FieldMapping] = {
    NodeType.CODE_JOB.value: FieldMapping(
        import_renames={"code_type": "language"},
        export_renames={"language": "code_type"},
    ),
    NodeType.DB.value: FieldMapping(
        import_renames={"source_details": "file"},
        export_renames={"file": "source_details"},
    ),
    # ... custom transforms for complex cases
}
```

**Usage:**
```python
props = NodeFieldMapper.map_import_fields(node_type, props)
props = NodeFieldMapper.map_export_fields(node_type, props)
```

### Specialized Utilities

**DiagramDataExtractor** (`utils/data_extractors.py`):
- Extracts nodes, arrows, handles, persons from diagrams
- Handles both dict and list formats
- Provides consistent interface for data extraction

**PersonReferenceResolver** (`utils/person_resolver.py`):
- Resolves person labels to IDs and vice versa
- Builds label↔ID mappings
- Updates node data with resolved references

**HandleIdOperations** (`utils/handle_operations.py`):
- Creates handle IDs from components
- Parses handle IDs to components
- Validates handle ID format
- Provides safe parsing with error handling

**ArrowBuilder** (`utils/arrow_builder.py`):
- Creates arrow dictionaries
- Handles arrow data processing
- Validates arrow structure

**NodeBuilder** (`utils/node_builder.py`):
- Creates node dictionaries
- Handles node data processing
- Ensures position data exists

## Strategy Pattern

DiPeO supports multiple diagram formats through a consistent strategy pattern:

```
strategies/
├── light/
│   ├── parser.py       # YAML/JSON → LightDiagram model
│   ├── transformer.py  # LightDiagram ↔ DomainDiagram
│   ├── serializer.py   # LightDiagram → YAML/JSON
│   └── strategy.py     # Orchestrates parser/transformer/serializer
└── readable/
    ├── parser.py       # Markdown → ReadableDiagram model
    ├── transformer.py  # ReadableDiagram ↔ DomainDiagram
    ├── serializer.py   # ReadableDiagram → Markdown
    └── strategy.py     # Orchestrates parser/transformer/serializer
```

### Strategy Components

**Parser:**
- Parses file format (YAML, JSON, Markdown) into format-specific model
- Validates format structure
- Extracts metadata

**Transformer:**
- Bidirectional conversion between format model and DomainDiagram
- Handles format-specific transformations (field mappings, handle generation)
- Preserves semantic information

**Serializer:**
- Converts format model to file format (YAML, JSON, Markdown)
- Ensures consistent formatting
- Handles optional fields

**Strategy:**
- Orchestrates parser → transformer → compiler flow
- Provides unified interface for format conversion
- Handles error propagation

### Adding New Formats

To add a new format:

1. Create `strategies/my_format/` directory
2. Implement `parser.py`, `transformer.py`, `serializer.py`, `strategy.py`
3. Follow the existing pattern (see light/ or readable/ as examples)
4. Register strategy in format registry

Example strategy interface:
```python
class MyFormatStrategy(FormatStrategy):
    def parse(self, file_path: str) -> MyFormatDiagram:
        """Parse file to format model"""
        pass

    def to_domain(self, my_diagram: MyFormatDiagram) -> DomainDiagram:
        """Convert to DomainDiagram"""
        pass

    def from_domain(self, domain_diagram: DomainDiagram) -> MyFormatDiagram:
        """Convert from DomainDiagram"""
        pass

    def serialize(self, my_diagram: MyFormatDiagram, file_path: str) -> None:
        """Write to file"""
        pass
```

## Error Handling

### CompilationResult

Compilation results contain structured error/warning information:

```python
@dataclass
class CompilationError:
    phase: CompilationPhase  # Which phase produced the error
    message: str             # Human-readable message
    node_id: str | None      # Related node ID (if applicable)
    arrow_id: str | None     # Related arrow ID (if applicable)

@dataclass
class CompilationResult:
    diagram: ExecutableDiagram | None
    errors: list[CompilationError]
    warnings: list[CompilationError]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
```

### Error Categories

**Validation Errors:**
- Structural issues (missing nodes, invalid IDs)
- Type errors (invalid node types)
- Connection errors (invalid handles, rule violations)

**Transformation Errors:**
- Node creation failures
- Field mapping errors
- Type conversion issues

**Resolution Errors:**
- Handle reference errors
- Connection parsing failures

**Edge Building Errors:**
- Edge creation failures
- Content type rule violations

**Optimization Errors:**
- Cycle detection
- Dependency graph errors

## Testing

### Unit Testing Phases

Test individual phases in isolation:

```python
from dipeo.domain.diagram.compilation.phases import (
    CompilationContext,
    ValidationPhase,
)

def test_validation_phase():
    context = CompilationContext(domain_diagram=test_diagram)
    phase = ValidationPhase()
    phase.execute(context)

    assert not context.result.errors
    assert len(context.nodes_list) > 0
```

### Integration Testing

Test full compilation pipeline:

```python
def test_full_compilation():
    compiler = DomainDiagramCompiler()
    result = compiler.compile_with_diagnostics(domain_diagram)

    assert result.is_valid
    assert result.diagram is not None
    assert len(result.diagram.nodes) > 0
```

### Partial Compilation

Stop after specific phase for testing:

```python
result = compiler.compile_with_diagnostics(
    domain_diagram,
    stop_after=CompilationPhase.VALIDATION
)
# Only validation phase ran, transformation and later phases skipped
```

## Performance Considerations

### Compilation Speed

Compilation is designed to be fast:
- Single-pass through most phases
- O(n) complexity for most operations
- Early exit on errors (no wasted work)

Typical compilation times:
- Small diagrams (< 10 nodes): < 10ms
- Medium diagrams (10-50 nodes): 10-50ms
- Large diagrams (50+ nodes): 50-200ms

### Memory Usage

Context object holds all intermediate state:
- Reuses data structures where possible
- Phases can access previous phase outputs
- Final diagram is self-contained

## Extending the Compiler

### Adding New Phases

To add a new compilation phase:

1. Create phase class in `compilation/phases/`
2. Inherit from `PhaseInterface`
3. Implement `execute()` and `phase_type` property
4. Add phase to compiler's phase list
5. Update `CompilationPhase` enum in `types.py`

Example:
```python
class MyCustomPhase(PhaseInterface):
    @property
    def phase_type(self) -> CompilationPhase:
        return CompilationPhase.MY_CUSTOM

    def execute(self, context: CompilationContext) -> None:
        # Read inputs from context
        nodes = context.typed_nodes

        # Perform transformations
        # ...

        # Report errors if needed
        context.result.add_error(
            self.phase_type,
            "Something went wrong",
            node_id="node_1"
        )

        # Write outputs to context
        context.my_custom_output = result
```

### Adding Node Type Support

To add support for a new node type:

1. **Define TypeScript spec** in `/dipeo/models/src/nodes/`
2. **Run codegen**: `cd dipeo/models && pnpm build && make codegen`
3. **Add handle configuration** in `utils/shared_components.py`:
   ```python
   HANDLE_SPECS: dict[str, list[HandleSpec]] = {
       NodeType.MY_NODE.value: [
           HandleSpec(HandleLabel.DEFAULT, HandleDirection.INPUT),
           HandleSpec(HandleLabel.DEFAULT, HandleDirection.OUTPUT),
       ],
   }
   ```
4. **Add field mappings** (if needed) in `utils/node_field_mapper.py`:
   ```python
   FIELD_MAPPINGS: dict[str, FieldMapping] = {
       NodeType.MY_NODE.value: FieldMapping(
           import_renames={"old_name": "new_name"},
       ),
   }
   ```
5. **Test compilation** with diagrams using the new node type

No changes needed in the compilation phases - they are node-type agnostic!

## Best Practices

1. **Keep phases focused**: Each phase should have one clear responsibility
2. **Report helpful errors**: Include context (node ID, arrow ID) in error messages
3. **Use configuration over code**: Prefer declarative tables over if-elif chains
4. **Test phases independently**: Unit test each phase before integration testing
5. **Follow the strategy pattern**: Keep parser/transformer/serializer separate
6. **Document field mappings**: Comment why field renames exist
7. **Validate early**: Catch errors in validation phase before transformation

## Related Documentation

- [Domain Layer Architecture](domain-layer.md) - Overview of domain organization
- [Diagram Execution](diagram-execution.md) - How compiled diagrams execute
- [Light Diagram Format](../formats/comprehensive_light_diagram_guide.md) - Format specification
- [Developer Guide](../guides/developer-guide-diagrams.md) - Practical development guide
