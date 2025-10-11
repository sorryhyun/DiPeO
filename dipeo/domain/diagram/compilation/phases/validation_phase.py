"""Validation phase for diagram compilation."""

from dipeo.diagram_generated import NodeType

from ...validation.utils import (
    validate_arrow_handles,
    validate_condition_node_branches,
    validate_node_type_connections,
)
from ..types import CompilationPhase
from .base import CompilationContext, PhaseInterface


class ValidationPhase(PhaseInterface):
    """Phase 1: Structural and semantic validation of the diagram."""

    @property
    def phase_type(self) -> CompilationPhase:
        return CompilationPhase.VALIDATION

    def execute(self, context: CompilationContext) -> None:
        """Validate diagram structure and semantics."""
        diagram = context.domain_diagram

        context.nodes_list = self._extract_nodes_list(diagram)
        context.arrows_list = self._extract_arrows_list(diagram)

        if not context.nodes_list:
            context.result.add_error(self.phase_type, "Diagram must contain at least one node")
            return

        self._validate_unique_node_ids(context)
        self._validate_node_types(context)
        self._validate_start_and_endpoint_nodes(context)
        self._validate_arrows(context)
        self._validate_node_connections(context)

    def _extract_nodes_list(self, diagram) -> list:
        """Extract nodes as a list from diagram."""
        if isinstance(diagram.nodes, dict):
            return list(diagram.nodes.values())
        return diagram.nodes

    def _extract_arrows_list(self, diagram) -> list:
        """Extract arrows as a list from diagram."""
        if isinstance(diagram.arrows, dict):
            return list(diagram.arrows.values())
        return diagram.arrows

    def _validate_unique_node_ids(self, context: CompilationContext) -> None:
        """Validate that all node IDs are unique."""
        node_ids = [node.id for node in context.nodes_list]
        if len(node_ids) != len(set(node_ids)):
            duplicates = [id for id in node_ids if node_ids.count(id) > 1]
            context.result.add_error(self.phase_type, f"Duplicate node IDs found: {duplicates}")

    def _validate_node_types(self, context: CompilationContext) -> None:
        """Validate that all nodes have valid NodeType enum values."""
        for node in context.nodes_list:
            try:
                if not isinstance(node.type, NodeType):
                    context.result.add_error(
                        self.phase_type,
                        f"Invalid node type: {node.type} (not a NodeType enum)",
                        node_id=node.id,
                    )
            except Exception as e:
                context.result.add_error(
                    self.phase_type,
                    f"Error validating node type: {node.type} - {e!s}",
                    node_id=node.id,
                )

    def _validate_start_and_endpoint_nodes(self, context: CompilationContext) -> None:
        """Validate presence of start and endpoint nodes."""
        start_nodes = [n for n in context.nodes_list if n.type == NodeType.START]
        endpoint_nodes = [n for n in context.nodes_list if n.type == NodeType.ENDPOINT]

        if not start_nodes:
            context.result.add_error(self.phase_type, "Diagram must have at least one start node")
        if not endpoint_nodes:
            context.result.add_warning(
                self.phase_type,
                "Diagram has no endpoint node - outputs may not be saved",
            )

    def _validate_arrows(self, context: CompilationContext) -> None:
        """Validate arrow handle references."""
        node_id_set = {node.id for node in context.nodes_list}

        for arrow in context.arrows_list:
            arrow_errors = validate_arrow_handles(arrow, node_id_set)
            for error in arrow_errors:
                context.result.add_error(self.phase_type, error, arrow_id=arrow.id)

    def _validate_node_connections(self, context: CompilationContext) -> None:
        """Validate node connection counts and condition branches."""
        node_id_set = {node.id for node in context.nodes_list}
        incoming_counts = {node.id: 0 for node in context.nodes_list}
        outgoing_counts = {node.id: 0 for node in context.nodes_list}
        outgoing_handles = {node.id: [] for node in context.nodes_list}

        for arrow in context.arrows_list:
            from dipeo.domain.diagram.utils import HandleIdOperations

            source_parsed = HandleIdOperations.parse_handle_id_safe(arrow.source)
            target_parsed = HandleIdOperations.parse_handle_id_safe(arrow.target)

            if source_parsed and target_parsed:
                if source_parsed.node_id in node_id_set:
                    outgoing_counts[source_parsed.node_id] += 1
                    if source_parsed.handle_label:
                        outgoing_handles[source_parsed.node_id].append(
                            source_parsed.handle_label.value
                        )
                if target_parsed.node_id in node_id_set:
                    incoming_counts[target_parsed.node_id] += 1

        for node in context.nodes_list:
            conn_errors = validate_node_type_connections(
                node, incoming_counts[node.id], outgoing_counts[node.id]
            )
            for error in conn_errors:
                context.result.add_error(self.phase_type, error, node_id=node.id)

            if node.type == NodeType.CONDITION:
                branch_warnings = validate_condition_node_branches(node, outgoing_handles[node.id])
                for warning in branch_warnings:
                    context.result.add_warning(self.phase_type, warning, node_id=node.id)
