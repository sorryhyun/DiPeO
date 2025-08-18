"""Domain-level diagram compiler with multi-phase compilation pipeline.

This compiler encapsulates all diagram compilation logic in the domain layer,
treating diagram compilation as a first-class domain concern with proper
phases, optimizations, and error handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from dipeo.application.migration.compat_imports import DiagramCompiler
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableEdgeV2
from dipeo.diagram_generated import DomainDiagram, NodeID, NodeType
from dipeo.diagram_generated.generated_nodes import ExecutableNode

from .connection_resolver import ConnectionResolver
from .edge_builder import EdgeBuilder
from .node_factory import NodeFactory
from ..validation.utils import (
    validate_arrow_handles,
    validate_node_type_connections,
    validate_condition_node_branches,
    find_unreachable_nodes,
)


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
    field_name: str | None = None  # For specific field validation
    
    def to_validation_error(self):
        """Convert to ValidationError for compatibility."""
        from dipeo.domain.base.exceptions import ValidationError
        field_name = self.field_name
        if not field_name:
            if self.node_id:
                field_name = f"node.{self.node_id}"
            elif self.arrow_id:
                field_name = f"arrow.{self.arrow_id}"
        return ValidationError(self.message, field_name=field_name)
    
    def to_validation_warning(self):
        """Convert to ValidationWarning for compatibility."""
        from dipeo.domain.validators.base_validator import ValidationWarning
        field_name = self.field_name
        if not field_name:
            if self.node_id:
                field_name = f"node.{self.node_id}"
            elif self.arrow_id:
                field_name = f"arrow.{self.arrow_id}"
        return ValidationWarning(self.message, field_name=field_name)


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
    
    def compile_with_diagnostics(
        self, 
        domain_diagram: DomainDiagram, 
        stop_after: CompilationPhase | None = None
    ) -> CompilationResult:
        """Compile with detailed diagnostics and error reporting.
        
        Args:
            domain_diagram: The diagram to compile
            stop_after: Optional phase to stop after (useful for validation-only)
        """
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
                if stop_after and phase == stop_after:
                    # Stop after requested phase
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
            return  # Can't continue without nodes
        
        # Check for duplicate node IDs
        node_ids = [node.id for node in context.nodes_list]
        if len(node_ids) != len(set(node_ids)):
            duplicates = [id for id in node_ids if node_ids.count(id) > 1]
            context.result.add_error(
                CompilationPhase.VALIDATION,
                f"Duplicate node IDs found: {duplicates}"
            )
        
        node_id_set = set(node_ids)
        
        # Validate node types
        for node in context.nodes_list:
            try:
                # Check if node.type is a valid NodeType enum
                if not isinstance(node.type, NodeType):
                    context.result.add_error(
                        CompilationPhase.VALIDATION,
                        f"Invalid node type: {node.type} (not a NodeType enum)",
                        node_id=node.id
                    )
            except Exception as e:
                context.result.add_error(
                    CompilationPhase.VALIDATION,
                    f"Error validating node type: {node.type} - {str(e)}",
                    node_id=node.id
                )
        
        # Validate start and endpoint nodes
        start_nodes = [n for n in context.nodes_list if n.type == NodeType.START]
        endpoint_nodes = [n for n in context.nodes_list if n.type == NodeType.ENDPOINT]
        
        if not start_nodes:
            context.result.add_error(
                CompilationPhase.VALIDATION,
                "Diagram must have at least one start node"
            )
        if not endpoint_nodes:
            context.result.add_warning(
                CompilationPhase.VALIDATION,
                "Diagram has no endpoint node - outputs may not be saved"
            )
        
        # Validate arrows using shared utilities
        for arrow in context.arrows_list:
            arrow_errors = validate_arrow_handles(arrow, node_id_set)
            for error in arrow_errors:
                context.result.add_error(
                    CompilationPhase.VALIDATION,
                    error,
                    arrow_id=arrow.id
                )
        
        # Count connections for each node
        incoming_counts = {node.id: 0 for node in context.nodes_list}
        outgoing_counts = {node.id: 0 for node in context.nodes_list}
        outgoing_handles = {node.id: [] for node in context.nodes_list}
        
        for arrow in context.arrows_list:
            from dipeo.domain.diagram.handle import parse_handle_id_safe
            source_parsed = parse_handle_id_safe(arrow.source)
            target_parsed = parse_handle_id_safe(arrow.target)
            
            if source_parsed and target_parsed:
                if source_parsed.node_id in node_id_set:
                    outgoing_counts[source_parsed.node_id] += 1
                    if source_parsed.handle_label:
                        outgoing_handles[source_parsed.node_id].append(source_parsed.handle_label.value)
                if target_parsed.node_id in node_id_set:
                    incoming_counts[target_parsed.node_id] += 1
        
        # Validate node type connection rules
        for node in context.nodes_list:
            # Check connection counts
            conn_errors = validate_node_type_connections(
                node,
                incoming_counts[node.id],
                outgoing_counts[node.id]
            )
            for error in conn_errors:
                context.result.add_error(
                    CompilationPhase.VALIDATION,
                    error,
                    node_id=node.id
                )
            
            # Check condition node branches
            if node.type == NodeType.CONDITION:
                branch_warnings = validate_condition_node_branches(
                    node,
                    outgoing_handles[node.id]
                )
                for warning in branch_warnings:
                    context.result.add_warning(
                        CompilationPhase.VALIDATION,
                        warning,
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
        # Detect unreachable nodes using shared utility
        unreachable = find_unreachable_nodes(context.nodes_list, context.arrows_list)
        
        for node_id in unreachable:
            # Skip START nodes in unreachable check (they are entry points)
            node = next((n for n in context.typed_nodes if n.id == node_id), None)
            if node and node.type != NodeType.START:
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
        
        # Extract persons data from domain diagram
        persons_metadata = {}
        if context.domain_diagram.persons:
            for person in context.domain_diagram.persons:
                person_data = {
                    'name': person.label,
                    'service': person.llm_config.service.value if hasattr(person.llm_config.service, 'value') else person.llm_config.service,
                    'model': person.llm_config.model,
                    'api_key_id': person.llm_config.api_key_id.value if hasattr(person.llm_config.api_key_id, 'value') else person.llm_config.api_key_id,
                }
                if hasattr(person.llm_config, 'temperature'):
                    person_data['temperature'] = person.llm_config.temperature
                if hasattr(person.llm_config, 'max_tokens'):
                    person_data['max_tokens'] = person.llm_config.max_tokens
                if hasattr(person.llm_config, 'system_prompt'):
                    person_data['system_prompt'] = person.llm_config.system_prompt
                persons_metadata[person.label] = person_data
        
        # Create metadata
        metadata = {
            "name": context.domain_diagram.metadata.name if context.domain_diagram.metadata else None,
            "compilation_warnings": [w.message for w in context.result.warnings],
            "start_nodes": list(context.start_nodes),
            "person_nodes": context.person_nodes,
            "node_dependencies": {k: list(v) for k, v in context.node_dependencies.items()},
            "persons": persons_metadata,  # Add persons metadata
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
        from dipeo.diagram_generated import (
            DomainNode, DomainArrow, DomainHandle, DomainPerson,
            Vec2, PersonLLMConfig, LLMService,
            HandleID, ArrowID, HandleLabel, HandleDirection, DataType, ApiKeyID,
            DiagramMetadata
        )
        
        # Convert typed nodes back to domain nodes
        domain_nodes = []
        for node in executable_diagram.nodes:
            # Create data dict from node attributes
            data = {}
            exclude_fields = {"id", "type", "position", "label", "flipped", "metadata"}
            for attr_name in dir(node):
                if not attr_name.startswith("_") and attr_name not in exclude_fields:
                    attr_value = getattr(node, attr_name, None)
                    if attr_value is not None and not callable(attr_value):
                        # Convert enums to their values for data field
                        if hasattr(attr_value, 'value'):
                            data[attr_name] = attr_value.value
                        elif hasattr(attr_value, 'model_dump'):
                            data[attr_name] = attr_value.model_dump()
                        else:
                            data[attr_name] = attr_value
            
            domain_node = DomainNode(
                id=node.id,
                type=node.type,
                position=Vec2(x=node.position.x, y=node.position.y),
                data=data
            )
            domain_nodes.append(domain_node)
        
        # Convert edges back to arrows with proper handle IDs
        arrows = []
        handles = []
        handle_id_counter = 0
        
        # Create handles for each edge connection
        for edge in executable_diagram.edges:
            # Create source handle ID
            source_handle_id = HandleID(f"handle_{handle_id_counter}")
            handle_id_counter += 1
            
            # Create target handle ID
            target_handle_id = HandleID(f"handle_{handle_id_counter}")
            handle_id_counter += 1
            
            # Create handles
            source_handle = DomainHandle(
                id=source_handle_id,
                node_id=edge.source_node_id,
                label=HandleLabel(edge.source_output),
                direction=HandleDirection.OUTPUT,
                data_type=DataType.ANY
            )
            handles.append(source_handle)
            
            target_handle = DomainHandle(
                id=target_handle_id,
                node_id=edge.target_node_id,
                label=HandleLabel(edge.target_input),
                direction=HandleDirection.INPUT,
                data_type=DataType.ANY
            )
            handles.append(target_handle)
            
            # Create arrow
            arrow = DomainArrow(
                id=ArrowID(edge.id),
                source=source_handle_id,
                target=target_handle_id,
                content_type=edge.content_type,
                data={"metadata": edge.metadata} if edge.metadata else None
            )
            arrows.append(arrow)
        
        # Extract persons from PersonJobNodes
        persons = []
        person_ids_seen = set()
        for node in executable_diagram.nodes:
            if isinstance(node, PersonJobNode) and hasattr(node, 'person_id'):
                person_id = node.person_id
                if person_id and person_id not in person_ids_seen:
                    person_ids_seen.add(person_id)
                    # Create a minimal person config for decompiled diagrams
                    persons.append(DomainPerson(
                        id=person_id,
                        label=person_id.capitalize(),
                        type="person",
                        llm_config=PersonLLMConfig(
                            service=LLMService.OPENAI,
                            model="gpt-5-nano-2025-08-07",
                            api_key_id=ApiKeyID("default")
                        )
                    ))
        
        # Convert metadata if it exists and is a dict
        metadata = None
        if executable_diagram.metadata:
            if isinstance(executable_diagram.metadata, DiagramMetadata):
                metadata = executable_diagram.metadata
            elif isinstance(executable_diagram.metadata, dict):
                # Create DiagramMetadata from dict if needed
                metadata = DiagramMetadata(
                    name=executable_diagram.metadata.get("name"),
                    description=executable_diagram.metadata.get("description"),
                    version=executable_diagram.metadata.get("version", "1.0"),
                    created=executable_diagram.metadata.get("created", ""),
                    modified=executable_diagram.metadata.get("modified", ""),
                    author=executable_diagram.metadata.get("author"),
                    tags=executable_diagram.metadata.get("tags"),
                    format=executable_diagram.metadata.get("format")
                )
        
        return DomainDiagram(
            nodes=domain_nodes,
            arrows=arrows,
            handles=handles,
            persons=persons,
            metadata=metadata
        )