"""Domain-level diagram compiler with multi-phase compilation pipeline.

This compiler encapsulates all diagram compilation logic in the domain layer,
treating diagram compilation as a first-class domain concern with proper
phases, optimizations, and error handling.
"""

from __future__ import annotations

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.domain.diagram.ports import DiagramCompiler

from .connection_resolver import ConnectionResolver
from .edge_builder import EdgeBuilder
from .node_factory import NodeFactory
from .phases import (
    AssemblyPhase,
    CompilationContext,
    ConnectionResolutionPhase,
    EdgeBuildingPhase,
    NodeTransformationPhase,
    OptimizationPhase,
    ValidationPhase,
)
from .types import CompilationPhase, CompilationResult


class DomainDiagramCompiler(DiagramCompiler):
    """Pure domain logic compiler with multi-phase compilation pipeline.

    This compiler orchestrates a series of compilation phases:
    1. Validation - Structural and semantic validation
    2. Transformation - Convert domain nodes to typed nodes
    3. Resolution - Resolve handle references to connections
    4. Edge Building - Create executable edges with rules
    5. Optimization - Optimize execution paths
    6. Assembly - Create final ExecutableDiagram
    """

    def __init__(self):
        node_factory = NodeFactory()
        connection_resolver = ConnectionResolver()
        edge_builder = EdgeBuilder()

        self.phases = [
            ValidationPhase(),
            NodeTransformationPhase(node_factory),
            ConnectionResolutionPhase(connection_resolver),
            EdgeBuildingPhase(edge_builder),
            OptimizationPhase(),
            AssemblyPhase(),
        ]

    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        result = self.compile_with_diagnostics(domain_diagram)

        if not result.is_valid:
            error_messages = [f"{e.phase.name}: {e.message}" for e in result.errors]
            raise ValueError("Compilation failed:\n" + "\n".join(error_messages))

        if result.diagram is None:
            raise RuntimeError("Compilation succeeded but no diagram was produced")
        return result.diagram

    def compile_with_diagnostics(
        self, domain_diagram: DomainDiagram, stop_after: CompilationPhase | None = None
    ) -> CompilationResult:
        """Compile with detailed diagnostics and error reporting.

        Args:
            domain_diagram: The diagram to compile
            stop_after: Optional phase to stop after (for testing/debugging)

        Returns:
            CompilationResult with diagram and diagnostics
        """
        context = CompilationContext(domain_diagram=domain_diagram)

        for phase in self.phases:
            try:
                phase.execute(context)

                if context.result.errors:
                    break

                if stop_after and phase.phase_type == stop_after:
                    break

            except Exception as e:
                context.result.add_error(phase.phase_type, f"Internal compiler error: {e!s}")
                break

        return context.result

    def decompile(self, executable_diagram: ExecutableDiagram) -> DomainDiagram:
        from dipeo.diagram_generated import (
            ApiKeyID,
            ArrowID,
            DataType,
            DiagramMetadata,
            DomainArrow,
            DomainHandle,
            DomainNode,
            DomainPerson,
            HandleDirection,
            HandleID,
            HandleLabel,
            LLMService,
            PersonLLMConfig,
            Vec2,
        )
        from dipeo.diagram_generated.generated_nodes import PersonJobNode

        domain_nodes = []
        for node in executable_diagram.nodes:
            data = {}
            exclude_fields = {"id", "type", "position", "label", "flipped", "metadata"}
            for attr_name in dir(node):
                if not attr_name.startswith("_") and attr_name not in exclude_fields:
                    attr_value = getattr(node, attr_name, None)
                    if attr_value is not None and not callable(attr_value):
                        if hasattr(attr_value, "value"):
                            data[attr_name] = attr_value.value
                        elif hasattr(attr_value, "model_dump"):
                            data[attr_name] = attr_value.model_dump()
                        else:
                            data[attr_name] = attr_value

            domain_node = DomainNode(
                id=node.id,
                type=node.type,
                position=Vec2(x=node.position.x, y=node.position.y),
                data=data,
            )
            domain_nodes.append(domain_node)

        arrows = []
        handles = []
        handle_id_counter = 0

        for edge in executable_diagram.edges:
            source_handle_id = HandleID(f"handle_{handle_id_counter}")
            handle_id_counter += 1

            target_handle_id = HandleID(f"handle_{handle_id_counter}")
            handle_id_counter += 1

            source_handle = DomainHandle(
                id=source_handle_id,
                node_id=edge.source_node_id,
                label=HandleLabel(edge.source_output),
                direction=HandleDirection.OUTPUT,
                data_type=DataType.ANY,
            )
            handles.append(source_handle)

            target_handle = DomainHandle(
                id=target_handle_id,
                node_id=edge.target_node_id,
                label=HandleLabel(edge.target_input),
                direction=HandleDirection.INPUT,
                data_type=DataType.ANY,
            )
            handles.append(target_handle)

            arrow = DomainArrow(
                id=ArrowID(edge.id),
                source=source_handle_id,
                target=target_handle_id,
                content_type=edge.content_type,
                data={"metadata": edge.metadata} if edge.metadata else None,
            )
            arrows.append(arrow)

        persons = []
        person_ids_seen = set()
        for node in executable_diagram.nodes:
            if isinstance(node, PersonJobNode) and hasattr(node, "person_id"):
                person_id = node.person_id
                if person_id and person_id not in person_ids_seen:
                    person_ids_seen.add(person_id)
                    persons.append(
                        DomainPerson(
                            id=person_id,
                            label=person_id.capitalize(),
                            type="person",
                            llm_config=PersonLLMConfig(
                                service=LLMService.OPENAI,
                                model="gpt-5-nano-2025-08-07",
                                api_key_id=ApiKeyID("default"),
                            ),
                        )
                    )

        metadata = None
        if executable_diagram.metadata:
            if isinstance(executable_diagram.metadata, DiagramMetadata):
                metadata = executable_diagram.metadata
            elif isinstance(executable_diagram.metadata, dict):
                metadata = DiagramMetadata(
                    id=executable_diagram.metadata.get("id"),
                    name=executable_diagram.metadata.get("name"),
                    description=executable_diagram.metadata.get("description"),
                    version=executable_diagram.metadata.get("version", "1.0"),
                    created=executable_diagram.metadata.get("created", ""),
                    modified=executable_diagram.metadata.get("modified", ""),
                    author=executable_diagram.metadata.get("author"),
                    tags=executable_diagram.metadata.get("tags"),
                    format=executable_diagram.metadata.get("format"),
                )

        return DomainDiagram(
            nodes=domain_nodes, arrows=arrows, handles=handles, persons=persons, metadata=metadata
        )
