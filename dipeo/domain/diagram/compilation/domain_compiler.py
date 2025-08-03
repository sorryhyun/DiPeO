"""Domain-level diagram compiler with multi-phase compilation pipeline.

This compiler encapsulates all diagram compilation logic in the domain layer,
treating diagram compilation as a first-class domain concern with proper
phases, optimizations, and error handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from dipeo.core.compilation.diagram_compiler import DiagramCompiler
from dipeo.core.compilation.executable_diagram import ExecutableDiagram, ExecutableEdgeV2
from dipeo.diagram_generated import DomainDiagram, NodeID, NodeType
from dipeo.diagram_generated.generated_nodes import ExecutableNode

from .connection_resolver import ConnectionResolver
from .edge_builder import EdgeBuilder
from .node_factory import NodeFactory


class CompilationPhase(Enum):
    """Phases of diagram compilation."""
    VALIDATION = auto()
    NODE_TRANSFORMATION = auto()
    CONNECTION_RESOLUTION = auto()
    EDGE_BUILDING = auto()
    OPTIMIZATION = auto()
    ASSEMBLY = auto()


@dataclass
class CompilationError:
    """Represents a compilation error with context."""
    phase: CompilationPhase
    message: str
    node_id: NodeID | None = None
    arrow_id: str | None = None
    severity: str = "error"  # error, warning, info
    suggestion: str | None = None


@dataclass
class CompilationResult:
    """Result of diagram compilation with diagnostics."""
    diagram: ExecutableDiagram | None
    errors: list[CompilationError] = field(default_factory=list)
    warnings: list[CompilationError] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_valid(self) -> bool:
        """Check if compilation succeeded without errors."""
        return self.diagram is not None and not self.errors
    
    @property
    def has_warnings(self) -> bool:
        """Check if compilation produced warnings."""
        return bool(self.warnings)
    
    def add_error(self, phase: CompilationPhase, message: str, **kwargs):
        """Add a compilation error."""
        self.errors.append(CompilationError(phase=phase, message=message, severity="error", **kwargs))
    
    def add_warning(self, phase: CompilationPhase, message: str, **kwargs):
        """Add a compilation warning."""
        self.warnings.append(CompilationError(phase=phase, message=message, severity="warning", **kwargs))


class CompilationContext:
    """Context passed through compilation phases."""
    
    def __init__(self, domain_diagram: DomainDiagram):
        self.domain_diagram = domain_diagram
        self.result = CompilationResult(diagram=None)
        
        # Phase outputs
        self.nodes_list: list[Any] = []
        self.arrows_list: list[Any] = []
        self.typed_nodes: list[ExecutableNode] = []
        self.node_map: dict[NodeID, ExecutableNode] = {}
        self.resolved_connections: list[Any] = []
        self.typed_edges: list[ExecutableEdgeV2] = []
        
        # Metadata
        self.start_nodes: set[NodeID] = set()
        self.person_nodes: dict[str, list[NodeID]] = {}
        self.node_dependencies: dict[NodeID, set[NodeID]] = {}


class DomainDiagramCompiler(DiagramCompiler):
    """Pure domain logic compiler with multi-phase compilation pipeline.
    
    This compiler encapsulates all compilation logic in the domain layer:
    1. Validation - Structural and semantic validation
    2. Transformation - Convert domain nodes to typed nodes
    3. Resolution - Resolve handle references to connections
    4. Edge Building - Create executable edges with rules
    5. Optimization - Optimize execution paths
    6. Assembly - Create final ExecutableDiagram
    """
    
    def __init__(self):
        self.node_factory = NodeFactory()
        self.connection_resolver = ConnectionResolver()
        self.edge_builder = EdgeBuilder()
    
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile domain diagram through all phases."""
        result = self.compile_with_diagnostics(domain_diagram)
        
        if not result.is_valid:
            # Convert errors to exception for backward compatibility
            error_messages = [f"{e.phase.name}: {e.message}" for e in result.errors]
            raise ValueError("Compilation failed:\n" + "\n".join(error_messages))
        
        if result.diagram is None:
            raise RuntimeError("Compilation succeeded but no diagram was produced")
        return result.diagram
    
    def compile_with_diagnostics(self, domain_diagram: DomainDiagram) -> CompilationResult:
        """Compile with detailed diagnostics and error reporting."""
        context = CompilationContext(domain_diagram)
        
        # Execute compilation phases
        phases = [
            (CompilationPhase.VALIDATION, self._validation_phase),
            (CompilationPhase.NODE_TRANSFORMATION, self._node_transformation_phase),
            (CompilationPhase.CONNECTION_RESOLUTION, self._connection_resolution_phase),
            (CompilationPhase.EDGE_BUILDING, self._edge_building_phase),
            (CompilationPhase.OPTIMIZATION, self._optimization_phase),
            (CompilationPhase.ASSEMBLY, self._assembly_phase),
        ]
        
        for phase, handler in phases:
            try:
                handler(context)
                if context.result.errors:
                    # Stop on first phase with errors
                    break
            except Exception as e:
                context.result.add_error(
                    phase,
                    f"Internal compiler error: {e!s}"
                )
                break
        
        return context.result
    
    def _validation_phase(self, context: CompilationContext) -> None:
        """Phase 1: Validate diagram structure and constraints."""
        diagram = context.domain_diagram
        
        # Extract nodes and arrows as lists
        context.nodes_list = self._extract_nodes_list(diagram)
        context.arrows_list = self._extract_arrows_list(diagram)
        
        # Basic validation
        if not context.nodes_list:
            context.result.add_error(
                CompilationPhase.VALIDATION,
                "Diagram must contain at least one node"
            )
        
        # Check for duplicate node IDs
        node_ids = [node.id for node in context.nodes_list]
        if len(node_ids) != len(set(node_ids)):
            duplicates = [id for id in node_ids if node_ids.count(id) > 1]
            context.result.add_error(
                CompilationPhase.VALIDATION,
                f"Duplicate node IDs found: {duplicates}"
            )
        
        # Validate node types
        for node in context.nodes_list:
            if not hasattr(NodeType, node.type.name):
                context.result.add_error(
                    CompilationPhase.VALIDATION,
                    f"Unknown node type: {node.type}",
                    node_id=node.id
                )
    
    def _node_transformation_phase(self, context: CompilationContext) -> None:
        """Phase 2: Transform domain nodes to strongly-typed executable nodes."""
        # Create typed nodes
        context.typed_nodes = self.node_factory.create_typed_nodes(context.nodes_list)
        
        # Collect factory errors
        for error in self.node_factory.get_validation_errors():
            context.result.add_error(
                CompilationPhase.NODE_TRANSFORMATION,
                error
            )
        
        # Build node map
        context.node_map = {node.id: node for node in context.typed_nodes}
        
        # Collect metadata
        for node in context.typed_nodes:
            if node.type == NodeType.START:
                context.start_nodes.add(node.id)
            elif node.type == NodeType.PERSON_JOB:
                person_id = getattr(node, 'person_id', None)
                if person_id:
                    if person_id not in context.person_nodes:
                        context.person_nodes[person_id] = []
                    context.person_nodes[person_id].append(node.id)
    
    def _connection_resolution_phase(self, context: CompilationContext) -> None:
        """Phase 3: Resolve handle references to node connections."""
        resolved, errors = self.connection_resolver.resolve_connections(
            context.arrows_list,
            context.nodes_list
        )
        
        context.resolved_connections = resolved
        
        # Collect resolver errors
        for error in errors:
            context.result.add_error(
                CompilationPhase.CONNECTION_RESOLUTION,
                error
            )
    
    def _edge_building_phase(self, context: CompilationContext) -> None:
        """Phase 4: Build executable edges with transformation rules."""
        edges, errors = self.edge_builder.build_edges(
            context.arrows_list,
            context.resolved_connections,
            context.node_map
        )
        
        context.typed_edges = edges
        
        # Collect builder errors
        for error in errors:
            context.result.add_error(
                CompilationPhase.EDGE_BUILDING,
                error
            )
        
        # Build dependency graph
        for edge in edges:
            if edge.target_node_id not in context.node_dependencies:
                context.node_dependencies[edge.target_node_id] = set()
            context.node_dependencies[edge.target_node_id].add(edge.source_node_id)
    
    def _optimization_phase(self, context: CompilationContext) -> None:
        """Phase 5: Optimize execution paths and detect issues."""
        # Detect unreachable nodes
        reachable = self._find_reachable_nodes(
            context.start_nodes,
            context.node_dependencies,
            context.typed_edges
        )
        
        for node in context.typed_nodes:
            if node.id not in reachable and node.type != NodeType.START:
                context.result.add_warning(
                    CompilationPhase.OPTIMIZATION,
                    f"Node '{node.id}' is unreachable from any start node",
                    node_id=node.id,
                    suggestion="Add a connection from a reachable node or start node"
                )
        
        # Detect cycles
        cycles = self._detect_cycles(context.node_dependencies)
        if cycles:
            context.result.add_warning(
                CompilationPhase.OPTIMIZATION,
                f"Circular dependencies detected: {cycles}",
                suggestion="Consider using condition nodes to break cycles"
            )
        
        # Analyze parallelization opportunities
        parallel_groups = self._analyze_parallel_execution(
            context.start_nodes,
            context.node_dependencies
        )
        if parallel_groups:
            context.result.metadata["parallel_groups"] = parallel_groups
    
    def _assembly_phase(self, context: CompilationContext) -> None:
        """Phase 6: Assemble the final ExecutableDiagram."""
        if context.result.errors:
            # Don't create diagram if there are errors
            return
        
        # Create metadata
        metadata = {
            "name": context.domain_diagram.metadata.name if context.domain_diagram.metadata else None,
            "compilation_warnings": [w.message for w in context.result.warnings],
            "start_nodes": list(context.start_nodes),
            "person_nodes": context.person_nodes,
            "node_dependencies": {k: list(v) for k, v in context.node_dependencies.items()},
            **context.result.metadata
        }
        
        # Create executable diagram
        context.result.diagram = ExecutableDiagram(
            nodes=context.typed_nodes,
            edges=context.typed_edges,
            execution_order=None,  # Dynamic ordering used
            metadata=metadata
        )
    
    # Helper methods
    
    def _extract_nodes_list(self, diagram: DomainDiagram) -> list:
        """Extract nodes as list from domain diagram."""
        if isinstance(diagram.nodes, dict):
            return list(diagram.nodes.values())
        return diagram.nodes
    
    def _extract_arrows_list(self, diagram: DomainDiagram) -> list:
        """Extract arrows as list from domain diagram."""
        if isinstance(diagram.arrows, dict):
            return list(diagram.arrows.values())
        return diagram.arrows
    
    def _find_reachable_nodes(
        self,
        start_nodes: set[NodeID],
        dependencies: dict[NodeID, set[NodeID]],
        edges: list[ExecutableEdgeV2]
    ) -> set[NodeID]:
        """Find all nodes reachable from start nodes."""
        reachable = set(start_nodes)
        
        # Build forward adjacency list
        forward_deps = {}
        for edge in edges:
            if edge.source_node_id not in forward_deps:
                forward_deps[edge.source_node_id] = set()
            forward_deps[edge.source_node_id].add(edge.target_node_id)
        
        # BFS from start nodes
        queue = list(start_nodes)
        while queue:
            node = queue.pop(0)
            if node in forward_deps:
                for target in forward_deps[node]:
                    if target not in reachable:
                        reachable.add(target)
                        queue.append(target)
        
        return reachable
    
    def _detect_cycles(self, dependencies: dict[NodeID, set[NodeID]]) -> list[list[NodeID]]:
        """Detect cycles in the dependency graph."""
        # Simple cycle detection - could be enhanced
        cycles = []
        
        def has_path(start: NodeID, end: NodeID, visited: set[NodeID]) -> bool:
            if start == end and visited:
                return True
            if start in visited:
                return False
            
            visited.add(start)
            return any(has_path(dep, end, visited.copy()) for dep in dependencies.get(start, set()))
        
        for node in dependencies:
            if has_path(node, node, set()):
                cycles.append([node])  # Simplified - could trace full cycle
        
        return cycles
    
    def _analyze_parallel_execution(
        self,
        start_nodes: set[NodeID],
        dependencies: dict[NodeID, set[NodeID]]
    ) -> list[set[NodeID]]:
        """Analyze which nodes can execute in parallel."""
        # Simple analysis - nodes with no dependencies between them
        # can execute in parallel
        parallel_groups = []
        
        # This is a simplified implementation
        # A real implementation would use topological sorting
        # and dependency analysis
        
        return parallel_groups
    
    def decompile(self, executable_diagram: ExecutableDiagram) -> DomainDiagram:
        """Convert executable diagram back to domain representation."""
        from dipeo.diagram_generated.generated_nodes import PersonJobNode
        
        # Convert typed nodes back to domain nodes
        domain_nodes = []
        for node in executable_diagram.nodes:
            domain_node = {
                "id": node.id,
                "type": node.type.value if hasattr(node.type, 'value') else node.type,
                "position": {"x": node.position.x, "y": node.position.y},
                "data": node.to_dict()
            }
            domain_nodes.append(domain_node)
        
        # Convert edges back to arrows
        arrows = []
        for edge in executable_diagram.edges:
            arrow = {
                "id": edge.id,
                "source": edge.source_node_id,
                "target": edge.target_node_id,
                "sourceHandle": edge.source_output,
                "targetHandle": edge.target_input,
                "metadata": getattr(edge, 'metadata', {})
            }
            arrows.append(arrow)
        
        # Extract handles from nodes
        handles = []
        
        # Extract persons from PersonJobNodes
        persons = []
        for node in executable_diagram.nodes:
            if isinstance(node, PersonJobNode) and node.person_id:
                persons.append({
                    "id": node.person_id,
                    "name": node.person_id.capitalize()
                })
        
        return DomainDiagram(
            nodes=domain_nodes,
            arrows=arrows,
            handles=handles,
            persons=persons,
            metadata=executable_diagram.metadata
        )