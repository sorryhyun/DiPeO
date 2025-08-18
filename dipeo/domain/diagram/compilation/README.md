# DiPeO Diagram Compilation Pipeline

## Overview

The `dipeo/domain/diagram/compilation` module implements the **diagram compilation pipeline** that transforms raw diagram definitions into executable form. It validates structure, resolves connections, builds edges with transformation rules, and produces type-safe executable diagrams ready for the execution engine.

## Architecture

### Compilation Pipeline Flow

```
Raw Diagram (JSON/YAML)
         │
         ▼
┌─────────────────────┐
│   Domain Compiler   │ ◄─── Orchestrates entire pipeline
└─────────┬───────────┘
          │
    ┌─────▼─────┐
    │   Phase 1 │ Node Creation
    │           │ (NodeFactory)
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │   Phase 2 │ Connection Resolution
    │           │ (ConnectionResolver)
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │   Phase 3 │ Edge Building
    │           │ (EdgeBuilder)
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │   Phase 4 │ Validation
    │           │ (Multiple Validators)
    └─────┬─────┘
          │
          ▼
  ExecutableDiagram
```

### Key Design Patterns

1. **Builder Pattern**: Step-by-step diagram construction
2. **Factory Pattern**: Node instance creation from specifications
3. **Strategy Pattern**: Different validation strategies
4. **Chain of Responsibility**: Multi-phase compilation
5. **Immutable Objects**: Compiled diagrams are immutable

## Core Components

### 1. Domain Compiler (`domain_compiler.py`)

Orchestrates the entire compilation process:

```python
class DomainDiagramCompiler(DiagramCompiler):
    """Main compiler orchestrating all compilation phases"""
    
    def compile(self, diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile domain diagram through all phases"""
        context = CompilationContext(diagram)
        
        # Phase 1: Create nodes
        nodes = self._create_nodes(context)
        
        # Phase 2: Resolve connections
        connections = self._resolve_connections(context, nodes)
        
        # Phase 3: Build edges
        edges = self._build_edges(context, connections)
        
        # Phase 4: Validate
        self._validate(context, nodes, edges)
        
        return ExecutableDiagram(nodes=nodes, edges=edges)
```

**Compilation Phases:**

```python
class CompilationPhase(Enum):
    INITIALIZATION = "initialization"
    NODE_CREATION = "node_creation"
    CONNECTION_RESOLUTION = "connection_resolution"
    EDGE_BUILDING = "edge_building"
    VALIDATION = "validation"
    FINALIZATION = "finalization"
```

**Compilation Context:**

```python
class CompilationContext:
    """Maintains state throughout compilation"""
    
    diagram: DomainDiagram          # Source diagram
    errors: list[CompilationError]  # Accumulated errors
    warnings: list[str]             # Compilation warnings
    metadata: dict[str, Any]        # Phase metadata
    node_registry: dict[str, Node]  # Created nodes
    edge_registry: dict[str, Edge]  # Built edges
```

### 2. Node Factory (`node_factory.py`)

Creates typed node instances from specifications:

```python
class NodeFactory:
    """Factory for creating typed node instances"""
    
    def create_node(self, node_spec: dict[str, Any]) -> ExecutableNode:
        """Create node instance from specification"""
        node_type = node_spec.get("type")
        
        # Map to specific node class
        node_class = self._get_node_class(node_type)
        
        # Validate specification
        self._validate_spec(node_spec, node_class)
        
        # Create instance with properties
        return node_class(
            id=node_spec["id"],
            type=node_type,
            properties=self._extract_properties(node_spec),
            metadata=self._extract_metadata(node_spec)
        )
    
    def batch_create(self, specs: list[dict]) -> dict[str, ExecutableNode]:
        """Create multiple nodes efficiently"""
```

**Node Type Mapping:**

```python
NODE_TYPE_MAP = {
    "PersonJob": PersonJobNode,
    "Condition": ConditionNode,
    "CodeJob": CodeJobNode,
    "ApiJob": ApiJobNode,
    "Start": StartNode,
    "Endpoint": EndpointNode,
    # ... more mappings
}
```

### 3. Connection Resolver (`connection_resolver.py`)

Validates and resolves connections between nodes:

```python
class ConnectionResolver:
    """Resolves and validates node connections"""
    
    def resolve_connections(self,
                           arrows: list[DomainArrow],
                           nodes: dict[str, ExecutableNode]) -> list[ResolvedConnection]:
        """Resolve all connections with validation"""
        resolved = []
        
        for arrow in arrows:
            # Validate source and target exist
            source_node = self._validate_node_exists(arrow.from_node, nodes)
            target_node = self._validate_node_exists(arrow.to_node, nodes)
            
            # Validate connection is allowed
            self._validate_connection_rules(source_node, target_node)
            
            # Resolve handle indices
            source_handle = self._resolve_handle(
                arrow.from_handle,
                source_node.output_handles
            )
            target_handle = self._resolve_handle(
                arrow.to_handle,
                target_node.input_handles
            )
            
            resolved.append(ResolvedConnection(
                source=source_node,
                target=target_node,
                source_handle=source_handle,
                target_handle=target_handle,
                metadata=arrow.metadata
            ))
        
        return resolved
```

**Connection Validation Rules:**

```python
class ConnectionRules:
    """Defines valid node type connections"""
    
    ALLOWED_CONNECTIONS = {
        NodeType.START: [NodeType.PERSON_JOB, NodeType.CONDITION, NodeType.CODE_JOB],
        NodeType.PERSON_JOB: [NodeType.PERSON_JOB, NodeType.CONDITION, NodeType.ENDPOINT],
        NodeType.CONDITION: [NodeType.PERSON_JOB, NodeType.CODE_JOB, NodeType.ENDPOINT],
        # ... more rules
    }
    
    @classmethod
    def can_connect(cls, source_type: NodeType, target_type: NodeType) -> bool:
        """Check if connection is allowed"""
        return target_type in cls.ALLOWED_CONNECTIONS.get(source_type, [])
```

### 4. Edge Builder (`edge_builder.py`)

Constructs executable edges with transformation rules:

```python
class EdgeBuilder:
    """Builds executable edges from resolved connections"""
    
    def build_edges(self,
                   connections: list[ResolvedConnection]) -> list[ExecutableEdgeV2]:
        """Build edges with transformation metadata"""
        edges = []
        
        for conn in connections:
            # Determine transformation rules
            transform_rules = self._determine_transformations(
                conn.source.type,
                conn.target.type,
                conn.source_handle,
                conn.target_handle
            )
            
            # Build edge with metadata
            edge = ExecutableEdgeV2(
                id=self._generate_edge_id(conn),
                source_node_id=conn.source.id,
                target_node_id=conn.target.id,
                source_handle=conn.source_handle,
                target_handle=conn.target_handle,
                transformation_metadata=TransformationMetadata(
                    rules=transform_rules,
                    source_type=conn.source.output_type,
                    target_type=conn.target.input_type
                )
            )
            
            edges.append(edge)
        
        return edges
```

**Transformation Metadata:**

```python
@dataclass
class TransformationMetadata:
    """Metadata for edge transformations"""
    rules: list[TransformRule]      # Transformation rules to apply
    source_type: str                # Source data type
    target_type: str                # Target data type
    validation_schema: dict | None   # Optional validation schema
    
    def is_compatible(self) -> bool:
        """Check if types are compatible"""
        return self.source_type == self.target_type or bool(self.rules)
```

## Compilation Process

### Phase 1: Node Creation

```python
def _create_nodes(self, context: CompilationContext) -> dict[str, ExecutableNode]:
    """Phase 1: Create all nodes"""
    nodes = {}
    
    for node_spec in context.diagram.nodes:
        try:
            node = self.node_factory.create_node(node_spec)
            nodes[node.id] = node
            context.node_registry[node.id] = node
        except Exception as e:
            context.errors.append(CompilationError(
                phase=CompilationPhase.NODE_CREATION,
                message=f"Failed to create node {node_spec.get('id')}: {e}"
            ))
    
    return nodes
```

### Phase 2: Connection Resolution

```python
def _resolve_connections(self,
                        context: CompilationContext,
                        nodes: dict[str, ExecutableNode]) -> list[ResolvedConnection]:
    """Phase 2: Resolve and validate connections"""
    try:
        connections = self.connection_resolver.resolve_connections(
            context.diagram.arrows,
            nodes
        )
        return connections
    except ConnectionError as e:
        context.errors.append(CompilationError(
            phase=CompilationPhase.CONNECTION_RESOLUTION,
            message=str(e)
        ))
        return []
```

### Phase 3: Edge Building

```python
def _build_edges(self,
                context: CompilationContext,
                connections: list[ResolvedConnection]) -> list[ExecutableEdgeV2]:
    """Phase 3: Build executable edges"""
    try:
        edges = self.edge_builder.build_edges(connections)
        
        # Store in context
        for edge in edges:
            context.edge_registry[edge.id] = edge
        
        return edges
    except Exception as e:
        context.errors.append(CompilationError(
            phase=CompilationPhase.EDGE_BUILDING,
            message=f"Edge building failed: {e}"
        ))
        return []
```

### Phase 4: Validation

```python
def _validate(self,
             context: CompilationContext,
             nodes: dict[str, ExecutableNode],
             edges: list[ExecutableEdgeV2]) -> None:
    """Phase 4: Comprehensive validation"""
    validators = [
        StructuralValidator(),      # Graph structure
        SemanticValidator(),        # Business rules
        CycleDetectionValidator(),  # No circular dependencies
        HandleValidator(),          # Handle compatibility
        TypeValidator()            # Type consistency
    ]
    
    for validator in validators:
        result = validator.validate(nodes, edges)
        context.errors.extend(result.errors)
        context.warnings.extend(result.warnings)
```

## Usage Examples

### Basic Compilation

```python
# Create compiler
compiler = DomainDiagramCompiler(
    node_factory=NodeFactory(),
    connection_resolver=ConnectionResolver(),
    edge_builder=EdgeBuilder()
)

# Compile diagram
domain_diagram = DomainDiagram.from_dict(diagram_dict)
executable_diagram = compiler.compile(domain_diagram)

# Check compilation result
if executable_diagram.is_valid():
    print(f"Compiled successfully: {len(executable_diagram.nodes)} nodes")
else:
    print(f"Compilation errors: {executable_diagram.compilation_errors}")
```

### Custom Node Factory

```python
class CustomNodeFactory(NodeFactory):
    """Extended factory with custom node types"""
    
    def __init__(self):
        super().__init__()
        self.register_node_type("CustomNode", CustomNode)
    
    def create_custom_node(self, spec: dict) -> CustomNode:
        """Create custom node with special handling"""
        node = super().create_node(spec)
        # Additional custom logic
        return node
```

### Connection Validation

```python
# Validate connections before compilation
resolver = ConnectionResolver()
validator = ConnectionValidator()

for arrow in diagram.arrows:
    if not validator.is_valid_connection(arrow.from_node, arrow.to_node):
        print(f"Invalid connection: {arrow.from_node} -> {arrow.to_node}")
```

### Transformation Rules

```python
# Define custom transformation
class JsonToYamlTransform(TransformRule):
    """Transform JSON data to YAML format"""
    
    def applies_to(self, source_type: str, target_type: str) -> bool:
        return source_type == "json" and target_type == "yaml"
    
    def transform(self, data: dict) -> str:
        return yaml.dump(data)

# Register transformation
edge_builder.register_transform(JsonToYamlTransform())
```

## Error Handling

### Compilation Errors

```python
@dataclass
class CompilationError:
    """Represents a compilation error"""
    phase: CompilationPhase
    message: str
    node_id: str | None = None
    severity: ErrorSeverity = ErrorSeverity.ERROR
    
    def is_fatal(self) -> bool:
        """Check if error prevents compilation"""
        return self.severity == ErrorSeverity.FATAL
```

### Error Recovery

```python
class CompilerWithRecovery(DomainDiagramCompiler):
    """Compiler with error recovery strategies"""
    
    def compile_with_recovery(self, diagram: DomainDiagram) -> CompilationResult:
        """Compile with automatic error recovery"""
        result = self.compile(diagram)
        
        if result.has_errors():
            # Try recovery strategies
            diagram = self._apply_recovery_strategies(diagram, result.errors)
            result = self.compile(diagram)
        
        return result
    
    def _apply_recovery_strategies(self, diagram, errors):
        """Apply recovery strategies for common errors"""
        # Remove invalid connections
        # Add missing handles
        # Fix type mismatches
        pass
```

## Best Practices

### 1. Fail-Fast Validation
- Validate early in each phase
- Accumulate all errors before failing
- Provide clear error messages with context

### 2. Immutability
- Compiled diagrams should be immutable
- Create new instances for modifications
- Use frozen dataclasses where appropriate

### 3. Type Safety
- Use typed node classes
- Validate properties against schemas
- Ensure handle type compatibility

### 4. Performance
- Cache compilation results
- Batch node creation
- Optimize connection resolution with indices

### 5. Extensibility
- Use factory pattern for new node types
- Register custom validators
- Support transformation plugins

## Testing

### Unit Tests

```python
def test_node_factory():
    """Test node creation"""
    factory = NodeFactory()
    spec = {"id": "node1", "type": "PersonJob", "properties": {...}}
    node = factory.create_node(spec)
    assert isinstance(node, PersonJobNode)
    assert node.id == "node1"

def test_connection_resolution():
    """Test connection validation"""
    resolver = ConnectionResolver()
    connections = resolver.resolve_connections(arrows, nodes)
    assert len(connections) == len(arrows)
    assert all(c.is_valid() for c in connections)
```

### Integration Tests

```python
def test_full_compilation():
    """Test complete compilation pipeline"""
    compiler = DomainDiagramCompiler()
    diagram = load_test_diagram("complex_workflow.yaml")
    
    result = compiler.compile(diagram)
    
    assert result.is_successful()
    assert len(result.executable_diagram.nodes) == 10
    assert len(result.executable_diagram.edges) == 15
```

## Dependencies

**Internal:**
- `dipeo.domain.diagram.models` - Domain diagram models
- `dipeo.domain.diagram.resolution` - Input resolution system (moved from domain root)
- `dipeo.diagram_generated` - Generated node types
- `dipeo.domain.execution` - Execution rules

**External:**
- Python 3.13+ standard library
- `dataclasses` - Data structures
- `enum` - Enumerations
- `typing` - Type hints

## Performance Considerations

- **Compilation Caching**: Cache compiled diagrams by hash
- **Parallel Validation**: Run validators concurrently
- **Lazy Edge Building**: Build edges on-demand for large diagrams
- **Incremental Compilation**: Recompile only changed sections
- **Memory Optimization**: Stream large diagrams during compilation

## Future Enhancements

- **Incremental Compilation**: Compile only changed portions
- **Compilation Optimization**: Remove unreachable nodes
- **Visual Debugging**: Generate compilation reports
- **Schema Evolution**: Support versioned node specifications
- **Compilation Plugins**: Extensible compilation phases