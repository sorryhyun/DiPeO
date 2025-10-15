# Developer Guide: Working with Diagrams

This guide provides practical instructions for developers working with DiPeO's diagram system.

## Quick Start

### Running Diagrams

```bash
# Run with debug logging
dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40

# Run with timing metrics
dipeo run examples/simple_diagrams/simple_iter --light --timing

# Run with custom input data
dipeo run my_diagram --light --input-data '{"key": "value"}'

# View metrics from latest run
dipeo metrics --latest --breakdown
```

### Exporting Diagrams to Python

```bash
# Export diagram to standalone Python script
dipeo export examples/simple_diagrams/simple_iter.light.yaml output.py --light

# Run exported script
python output.py
```

## Adding New Node Types

The system uses configuration-driven approaches - no need to modify compilation logic!

### Step 1: Define TypeScript Spec

Create a spec in `/dipeo/models/src/nodes/my_node.spec.ts`:

```typescript
export const MyNodeSpec = {
  type: 'my_node',
  fields: {
    input_text: { type: 'string', required: true },
    max_length: { type: 'number', default: 100 },
    enabled: { type: 'boolean', default: true }
  }
};
```

### Step 2: Run Code Generation

```bash
cd dipeo/models && pnpm build
make codegen
make diff-staged    # Review changes
make apply-test     # Apply with validation
```

This generates:
- Pydantic models in `/dipeo/diagram_generated/`
- GraphQL types
- TypeScript types for frontend

### Step 3: Configure Handles

Add handle configuration in `/dipeo/domain/diagram/utils/shared_components.py`:

```python
HANDLE_SPECS: dict[str, list[HandleSpec]] = {
    NodeType.MY_NODE.value: [
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.INPUT),
        HandleSpec(HandleLabel.DEFAULT, HandleDirection.OUTPUT),
        # Add custom handles if needed:
        HandleSpec(HandleLabel.SUCCESS, HandleDirection.OUTPUT, DataType.BOOLEAN),
        HandleSpec(HandleLabel.ERROR, HandleDirection.OUTPUT, DataType.STRING),
    ],
}
```

**Common Handle Patterns:**
- **Simple nodes**: One input, one output (default)
- **Start nodes**: Output only
- **End nodes**: Input only
- **Conditional nodes**: One input, multiple labeled outputs
- **Multi-input nodes**: Multiple inputs (FIRST + DEFAULT for person_job)

### Step 4: Add Field Mappings (Optional)

If your node needs field renaming between formats, add to `/dipeo/domain/diagram/utils/node_field_mapper.py`:

```python
FIELD_MAPPINGS: dict[str, FieldMapping] = {
    NodeType.MY_NODE.value: FieldMapping(
        # Rename fields during import (light → domain)
        import_renames={"old_field_name": "new_field_name"},

        # Set default values for missing fields
        import_defaults={"optional_field": "default_value"},

        # Remove fields not in domain model
        import_removes=["deprecated_field"],

        # Rename fields during export (domain → light)
        export_renames={"new_field_name": "old_field_name"},

        # Custom transformation function (for complex cases)
        custom_import=lambda props: {
            **props,
            "computed_field": props["a"] + props["b"]
        },
    ),
}
```

**When to use field mappings:**
- Light format uses different field names than domain model
- Need to provide default values for backward compatibility
- Complex transformations between formats (e.g., splitting/joining fields)

### Step 5: Create Node Handler

Create handler in `/dipeo/application/execution/handlers/my_node.py`:

```python
from dipeo.application.execution.handlers.base import TypedNodeHandler, register_handler
from dipeo.diagram_generated.generated_nodes import MyNodeNode
from dipeo.domain.execution.models import Envelope, ExecutionRequest

@register_handler
class MyNodeHandler(TypedNodeHandler[MyNodeNode]):
    """Handler for my_node nodes."""

    def prepare_inputs(self, inputs: dict, request: ExecutionRequest) -> dict:
        """Transform Envelope inputs to handler format."""
        # Extract text from input envelope
        input_text = inputs.get("default", {}).get("body", "")
        return {"input_text": input_text}

    async def run(self, inputs: dict, request: ExecutionRequest) -> str:
        """Execute the node's business logic."""
        input_text = inputs["input_text"]
        max_length = request.node.max_length

        # Your logic here
        result = input_text[:max_length]
        return result

    def serialize_output(self, result: str, request: ExecutionRequest) -> Envelope:
        """Convert result to Envelope."""
        from dipeo.domain.execution.envelope_factory import EnvelopeFactory
        return EnvelopeFactory.create(result, produced_by=request.node.id)

    async def on_error(self, request: ExecutionRequest, error: Exception) -> Envelope | None:
        """Handle errors gracefully."""
        from dipeo.domain.execution.envelope_factory import EnvelopeFactory
        return EnvelopeFactory.create_error(str(error), produced_by=request.node.id)
```

### Step 6: Update GraphQL Schema

```bash
make graphql-schema
```

This regenerates GraphQL types and TypeScript hooks for the frontend.

### Step 7: Test

Create a test diagram in `examples/test_my_node.light.yaml`:

```yaml
nodes:
  - type: start
    label: Start
  - type: my_node
    label: MyNode
    input_text: "Hello, World!"
    max_length: 5
  - type: endpoint
    label: End

connections:
  - from: Start
    to: MyNode
  - from: MyNode
    to: End
```

Test it:
```bash
dipeo run examples/test_my_node --light --debug
```

## Adding New Diagram Formats

DiPeO supports multiple diagram formats through a consistent strategy pattern.

### Format Strategy Structure

Create `strategies/my_format/` directory with four files:

```
strategies/my_format/
├── parser.py       # File → Format Model
├── transformer.py  # Format Model ↔ DomainDiagram
├── serializer.py   # Format Model → File
└── strategy.py     # Orchestration
```

### Step 1: Define Format Model

In `models/format_models.py`:

```python
from pydantic import BaseModel

class MyFormatNode(BaseModel):
    name: str
    type: str
    config: dict = {}

class MyFormatDiagram(BaseModel):
    version: str
    nodes: list[MyFormatNode]
    edges: list[tuple[str, str]]
```

### Step 2: Implement Parser

In `strategies/my_format/parser.py`:

```python
from dipeo.domain.diagram.models.format_models import MyFormatDiagram

class MyFormatParser:
    """Parse my_format files to MyFormatDiagram model."""

    def parse(self, content: str) -> MyFormatDiagram:
        """Parse file content to format model."""
        # Your parsing logic (JSON, YAML, custom format, etc.)
        data = parse_my_format(content)
        return MyFormatDiagram(**data)

    def parse_file(self, file_path: str) -> MyFormatDiagram:
        """Parse file to format model."""
        with open(file_path) as f:
            content = f.read()
        return self.parse(content)
```

### Step 3: Implement Transformer

In `strategies/my_format/transformer.py`:

```python
from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.models.format_models import MyFormatDiagram
from dipeo.domain.diagram.utils import (
    create_node_id,
    nodes_list_to_dict,
    arrows_list_to_dict,
    HandleIdOperations,
)

class MyFormatTransformer:
    """Transform between MyFormat and Domain models."""

    def to_domain(self, my_diagram: MyFormatDiagram) -> dict:
        """Convert MyFormatDiagram to DomainDiagram dict."""
        nodes_list = []
        for idx, node in enumerate(my_diagram.nodes):
            nodes_list.append({
                "id": create_node_id(idx),
                "type": node.type,
                "position": {"x": 0, "y": idx * 100},
                "data": node.config,
            })

        arrows_list = []
        for idx, (from_name, to_name) in enumerate(my_diagram.edges):
            # Find node IDs by name
            from_id = self._find_node_id(nodes_list, from_name)
            to_id = self._find_node_id(nodes_list, to_name)

            # Create handle IDs
            source_handle_id, target_handle_id = HandleIdOperations.create_handle_ids(
                from_id, to_id, "default", "default"
            )

            arrows_list.append({
                "id": f"arrow_{idx}",
                "source": source_handle_id,
                "target": target_handle_id,
            })

        return {
            "nodes": nodes_list_to_dict(nodes_list),
            "arrows": arrows_list_to_dict(arrows_list),
            "handles": {},
            "persons": {},
        }

    def from_domain(self, domain_diagram: DomainDiagram) -> MyFormatDiagram:
        """Convert DomainDiagram to MyFormatDiagram."""
        nodes = []
        for node in domain_diagram.nodes:
            nodes.append(MyFormatNode(
                name=node.data.get("label", node.id),
                type=node.type.value,
                config=node.data,
            ))

        edges = []
        for arrow in domain_diagram.arrows:
            from_id, _, _ = HandleIdOperations.parse_handle_id(arrow.source)
            to_id, _, _ = HandleIdOperations.parse_handle_id(arrow.target)
            edges.append((from_id, to_id))

        return MyFormatDiagram(
            version="1.0",
            nodes=nodes,
            edges=edges,
        )

    def _find_node_id(self, nodes: list, name: str) -> str:
        """Find node ID by name."""
        for node in nodes:
            if node["data"].get("label") == name:
                return node["id"]
        raise ValueError(f"Node not found: {name}")
```

### Step 4: Implement Serializer

In `strategies/my_format/serializer.py`:

```python
from dipeo.domain.diagram.models.format_models import MyFormatDiagram

class MyFormatSerializer:
    """Serialize MyFormatDiagram to file format."""

    def serialize(self, diagram: MyFormatDiagram) -> str:
        """Serialize diagram to string."""
        # Your serialization logic (JSON, YAML, custom format, etc.)
        return serialize_my_format(diagram)

    def serialize_to_file(self, diagram: MyFormatDiagram, file_path: str) -> None:
        """Serialize diagram to file."""
        content = self.serialize(diagram)
        with open(file_path, 'w') as f:
            f.write(content)
```

### Step 5: Implement Strategy

In `strategies/my_format/strategy.py`:

```python
from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.strategies.base import FormatStrategy
from .parser import MyFormatParser
from .transformer import MyFormatTransformer
from .serializer import MyFormatSerializer

class MyFormatStrategy(FormatStrategy):
    """Strategy for my_format diagram format."""

    def __init__(self):
        self.parser = MyFormatParser()
        self.transformer = MyFormatTransformer()
        self.serializer = MyFormatSerializer()

    def parse(self, file_path: str) -> DomainDiagram:
        """Parse file to DomainDiagram."""
        # Parse file to format model
        format_diagram = self.parser.parse_file(file_path)

        # Transform to domain dict
        domain_dict = self.transformer.to_domain(format_diagram)

        # Validate and create DomainDiagram
        return DomainDiagram(**domain_dict)

    def serialize(self, domain_diagram: DomainDiagram, file_path: str) -> None:
        """Serialize DomainDiagram to file."""
        # Transform to format model
        format_diagram = self.transformer.from_domain(domain_diagram)

        # Serialize to file
        self.serializer.serialize_to_file(format_diagram, file_path)
```

### Step 6: Register Strategy

In format registry (location varies based on your setup):

```python
FORMAT_STRATEGIES = {
    "light": LightStrategy(),
    "readable": ReadableStrategy(),
    "my_format": MyFormatStrategy(),  # Add your strategy
}
```

## Working with Compilation

### Understanding Compilation Phases

The compiler runs 6 phases in sequence:

1. **Validation** - Check structure and semantics
2. **Transformation** - Convert to typed nodes
3. **Resolution** - Resolve handle references
4. **Edge Building** - Create edges with rules
5. **Optimization** - Build dependency graph
6. **Assembly** - Create ExecutableDiagram

Each phase can report errors/warnings independently.

### Getting Compilation Diagnostics

```python
from dipeo.domain.diagram.compilation import DomainDiagramCompiler

compiler = DomainDiagramCompiler()
result = compiler.compile_with_diagnostics(domain_diagram)

if not result.is_valid:
    print("Compilation failed:")
    for error in result.errors:
        print(f"  [{error.phase.name}] {error.message}")
        if error.node_id:
            print(f"    Node: {error.node_id}")

for warning in result.warnings:
    print(f"  Warning [{warning.phase.name}] {warning.message}")
```

### Testing Compilation Phases

Test individual phases:

```python
from dipeo.domain.diagram.compilation.phases import (
    CompilationContext,
    ValidationPhase,
)

def test_validation():
    context = CompilationContext(domain_diagram=test_diagram)
    phase = ValidationPhase()
    phase.execute(context)

    assert not context.result.errors
    assert len(context.nodes_list) == expected_count
```

Test partial compilation (stop after specific phase):

```python
from dipeo.domain.diagram.compilation.types import CompilationPhase

result = compiler.compile_with_diagnostics(
    domain_diagram,
    stop_after=CompilationPhase.VALIDATION
)
# Only validation runs, useful for testing validation logic
```

### Adding Custom Compilation Phase

See [Diagram Compilation Architecture](../architecture/detailed/diagram-compilation.md#extending-the-compiler) for details.

## Testing Diagrams

### Unit Tests

Test diagram compilation:

```python
def test_simple_diagram_compiles():
    from dipeo.domain.diagram.compilation import DomainDiagramCompiler

    compiler = DomainDiagramCompiler()
    result = compiler.compile_with_diagnostics(simple_diagram)

    assert result.is_valid
    assert result.diagram is not None
    assert len(result.diagram.nodes) == 3
```

### Integration Tests

Test end-to-end execution:

```python
async def test_diagram_execution():
    # Load and compile diagram
    strategy = LightStrategy()
    domain_diagram = strategy.parse("test_diagram.light.yaml")
    compiler = DomainDiagramCompiler()
    executable_diagram = compiler.compile(domain_diagram)

    # Execute diagram
    from dipeo.application.execution import ExecuteDiagramUseCase

    executor = ExecuteDiagramUseCase(service_registry)
    result = await executor.execute(executable_diagram, input_data={})

    assert result.status == "completed"
    assert "output" in result.outputs
```

### CLI Testing

```bash
# Test diagram runs without errors
dipeo run examples/my_test_diagram --light --debug

# Test with timing to catch performance issues
dipeo run examples/my_test_diagram --light --timing

# Test export round-trip
dipeo export examples/my_test_diagram.light.yaml /tmp/test.py --light
python /tmp/test.py
```

## Common Patterns

### Adding Custom Validation

Add validation in the appropriate phase or create custom phase:

```python
class MyCustomValidationPhase(PhaseInterface):
    @property
    def phase_type(self) -> CompilationPhase:
        return CompilationPhase.VALIDATION

    def execute(self, context: CompilationContext) -> None:
        for node in context.nodes_list:
            if node.type == NodeType.MY_NODE:
                if not self._validate_my_node(node):
                    context.result.add_error(
                        self.phase_type,
                        "My node validation failed",
                        node_id=node.id
                    )
```

### Handling Complex Field Transformations

Use custom transformation functions in field mappings:

```python
def complex_import_transform(props: dict) -> dict:
    # Split combined field
    if "combined_field" in props:
        parts = props.pop("combined_field").split(":")
        props["field_a"] = parts[0]
        props["field_b"] = parts[1] if len(parts) > 1 else ""

    # Convert legacy format
    if "old_config" in props:
        old = props.pop("old_config")
        props["new_config"] = {
            "enabled": old.get("active", False),
            "value": old.get("val", 0),
        }

    return props

FIELD_MAPPINGS = {
    NodeType.MY_NODE.value: FieldMapping(
        custom_import=complex_import_transform,
    ),
}
```

### Creating Utility Functions

Add reusable utilities to `/dipeo/domain/diagram/utils/`:

```python
# utils/my_utils.py
def extract_node_property(node: dict, property_path: str, default=None):
    """Extract nested property from node using dot notation."""
    parts = property_path.split(".")
    current = node.get("data", {})
    for part in parts:
        if not isinstance(current, dict):
            return default
        current = current.get(part)
        if current is None:
            return default
    return current
```

## Debugging

### Debug Logging

Enable debug logging:

```bash
# CLI
dipeo run my_diagram --light --debug

# Check logs
tail -f .dipeo/logs/cli.log
```

In Python:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Compilation Errors

When compilation fails:

1. Check which phase failed (error message includes phase name)
2. Review the specific error message
3. Check node/arrow ID if provided
4. Use partial compilation to isolate the issue:

```python
result = compiler.compile_with_diagnostics(
    diagram,
    stop_after=CompilationPhase.VALIDATION
)
```

### Execution Errors

When execution fails:

1. Check GraphQL subscription for real-time events
2. Review execution logs in `.dipeo/logs/`
3. Use `--debug` flag for detailed logging
4. Check metrics: `dipeo metrics --latest --breakdown`

## Performance

### Compilation Performance

Compilation is fast:
- Small diagrams (< 10 nodes): < 10ms
- Medium diagrams (10-50 nodes): 10-50ms
- Large diagrams (50+ nodes): 50-200ms

If compilation is slow:
1. Check for excessive validation rules
2. Profile specific phases
3. Optimize field transformations

### Execution Performance

Configure concurrency in `/dipeo/config/execution.py`:

```python
ENGINE_MAX_CONCURRENT = 20      # Max concurrent nodes
BATCH_MAX_CONCURRENT = 10       # Max concurrent batch items
SUB_DIAGRAM_MAX_CONCURRENT = 10 # Max concurrent sub-diagrams
```

## Best Practices

1. **Use configuration over code**: Prefer HANDLE_SPECS and FIELD_MAPPINGS over if-elif chains
2. **Test incrementally**: Test each phase independently before integration
3. **Follow naming conventions**: Use snake_case for Python, camelCase for TypeScript/GraphQL
4. **Document field mappings**: Comment why field renames exist
5. **Handle errors gracefully**: Provide helpful error messages with context
6. **Use the strategy pattern**: Keep parser/transformer/serializer separate
7. **Leverage utilities**: Use existing utilities from utils/ instead of reimplementing
8. **Run linting**: `make lint-server` before committing

## Common Issues

### "Invalid node type" Error

Cause: Node type not in NodeType enum

Solution:
1. Check TypeScript spec is defined
2. Run codegen: `make codegen && make apply-test`
3. Update GraphQL schema: `make graphql-schema`

### "Handle not found" Error

Cause: Arrow references non-existent handle

Solution:
1. Check HANDLE_SPECS includes the handle label
2. Verify arrow references correct handle IDs
3. Use HandleIdOperations to create valid handle IDs

### Field Mapping Not Working

Cause: Field mapping not applied or incorrect

Solution:
1. Check FIELD_MAPPINGS includes your node type
2. Verify mapping keys match field names exactly
3. Test with debug logging to see actual field values
4. Use custom_import for complex transformations

### Compilation Succeeds but Execution Fails

Cause: Runtime error in node handler

Solution:
1. Check handler implementation
2. Verify prepare_inputs extracts data correctly
3. Use try-except in handler run() method
4. Implement on_error() for graceful failure handling

## Further Reading

- [Diagram Compilation Architecture](../architecture/detailed/diagram-compilation.md) - Detailed compilation architecture
- [Light Diagram Format](../formats/comprehensive_light_diagram_guide.md) - Format specification
- [Code Generation Guide](../projects/code-generation-guide.md) - Codegen workflow
