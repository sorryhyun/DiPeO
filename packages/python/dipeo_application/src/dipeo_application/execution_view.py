"""Simplified execution view for local execution."""

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional

from dipeo_domain.models import DomainArrow, DomainDiagram, DomainNode, NodeOutput


@dataclass
class NodeView:
    """View of a node with its execution context."""

    node: DomainNode
    handler: Optional[Callable] = None
    incoming_edges: List["EdgeView"] = field(default_factory=list)
    outgoing_edges: List["EdgeView"] = field(default_factory=list)
    output: Optional[NodeOutput] = None
    exec_count: int = 0

    @property
    def id(self) -> str:
        return self.node.id

    @property
    def type(self) -> str:
        return self.node.type

    @property
    def data(self) -> Dict[str, Any]:
        return self.node.data or {}

    def get_input_values(self) -> Dict[str, Any]:
        """Get input values from connected nodes."""
        inputs = {}
        for edge in self.incoming_edges:
            if edge.source_view.output:
                value = edge.source_view.output.value.get(edge.label, None)
                if value is not None:
                    inputs[edge.label] = value
        return inputs

    def get_active_inputs(self) -> Dict[str, Any]:
        """Get inputs considering condition routing and person_job first/default logic."""
        inputs = {}

        # Separate first/default edges for person_job nodes
        first_edges = []
        default_edges = []

        for edge in self.incoming_edges:
            if edge.source_view.output is None:
                continue

            if edge.target_handle == "first":
                first_edges.append(edge)
            else:
                default_edges.append(edge)

        # Select edges based on node type and execution count
        if self.node.type == "person_job":
            if self.exec_count == 0 and first_edges:
                selected_edges = first_edges
            else:
                selected_edges = default_edges
        else:
            selected_edges = first_edges + default_edges

        # Process selected edges
        for edge in selected_edges:
            # Handle condition node branching
            if edge.source_view.node.type == "condition":
                condition_result = edge.source_view.output.metadata.get(
                    "condition_result", False
                )
                edge_branch = edge.arrow.data.get("branch") if edge.arrow.data else None

                if edge_branch is not None:
                    edge_branch_bool = edge_branch.lower() == "true"
                    if edge_branch_bool != condition_result:
                        continue

            # Extract value
            label = edge.label
            source_values = edge.source_view.output.value

            if label in source_values:
                inputs[label] = source_values[label]
            elif label == "default" and "conversation" in source_values:
                # Special case for conversation passthrough
                inputs[label] = source_values["conversation"]

        return inputs


@dataclass
class EdgeView:
    """View of an edge (arrow) connecting two nodes."""

    arrow: DomainArrow
    source_view: NodeView
    target_view: NodeView

    @property
    def source_handle(self) -> str:
        parts = self.arrow.source.split(":", 1)
        return parts[1] if len(parts) > 1 else "default"

    @property
    def target_handle(self) -> str:
        parts = self.arrow.target.split(":", 1)
        return parts[1] if len(parts) > 1 else "default"

    @property
    def label(self) -> str:
        if self.arrow.data and isinstance(self.arrow.data, dict):
            return self.arrow.data.get("label", "default")
        return "default"

    @property
    def content_type(self) -> str:
        if self.arrow.data and isinstance(self.arrow.data, dict):
            return self.arrow.data.get("contentType", "raw_text")
        return "raw_text"


class LocalExecutionView:
    """Simplified execution view for local execution."""

    def __init__(self, diagram: DomainDiagram):
        self.diagram = diagram
        self.node_views: Dict[str, NodeView] = {}
        self.edge_views: List[EdgeView] = []

        self._build_views()
        self.execution_order = self._compute_execution_order()

    def _build_views(self) -> None:
        """Build node and edge views from diagram."""
        # Create node views
        for node in self.diagram.nodes:
            node_view = NodeView(node=node)
            self.node_views[node.id] = node_view

        # Create edge views and connect nodes
        import logging

        log = logging.getLogger(__name__)
        for arrow in self.diagram.arrows:
            source_id = arrow.source.split(":")[0]
            target_id = arrow.target.split(":")[0]

            if source_id in self.node_views and target_id in self.node_views:
                edge_view = EdgeView(
                    arrow=arrow,
                    source_view=self.node_views[source_id],
                    target_view=self.node_views[target_id],
                )

                self.edge_views.append(edge_view)
                self.node_views[source_id].outgoing_edges.append(edge_view)
                self.node_views[target_id].incoming_edges.append(edge_view)
                pass  # Removed debug log

    def _compute_execution_order(self) -> List[List[NodeView]]:
        """Compute topological execution order using Kahn's algorithm."""
        import logging

        log = logging.getLogger(__name__)

        # Calculate in-degrees
        in_degree = {}
        for node_id, node_view in self.node_views.items():
            # For person_job nodes, only count "first" edges for initial execution
            if node_view.node.type == "person_job":
                first_edges = [
                    e for e in node_view.incoming_edges if e.target_handle == "first"
                ]
                if first_edges:
                    in_degree[node_id] = len(first_edges)
                else:
                    in_degree[node_id] = len(node_view.incoming_edges)
            else:
                in_degree[node_id] = len(node_view.incoming_edges)
            pass  # Removed debug log

        # Find nodes with no dependencies
        queue = [nv for nid, nv in self.node_views.items() if in_degree[nid] == 0]
        # Initial queue computed
        levels = []
        processed = set()

        # Process levels
        while queue:
            current_level = queue[:]
            levels.append(current_level)
            next_queue = []

            for node_view in current_level:
                processed.add(node_view.id)
                for edge in node_view.outgoing_edges:
                    target_id = edge.target_view.id
                    target_view = edge.target_view

                    # Only decrement if this edge matters for initial execution
                    should_decrement = True
                    if (
                        target_view.node.type == "person_job"
                        and edge.target_handle != "first"
                    ):
                        # For person_job nodes, only "first" edges matter for initial topological sort
                        first_edges = [
                            e
                            for e in target_view.incoming_edges
                            if e.target_handle == "first"
                        ]
                        if first_edges:
                            should_decrement = False

                    if should_decrement:
                        in_degree[target_id] -= 1

                        if in_degree[target_id] == 0:
                            next_queue.append(edge.target_view)

            queue = next_queue
            # Level processed

        # Check for unprocessed nodes
        unprocessed = set(self.node_views.keys()) - processed
        if unprocessed:
            log.warning(f"Nodes not included in execution order: {unprocessed}")

        return levels

    def get_node_view(self, node_id: str) -> Optional[NodeView]:
        """Get node view by ID."""
        return self.node_views.get(node_id)

    def get_ready_nodes(self) -> List[NodeView]:
        """Get nodes that are ready to execute."""
        ready = []
        for node_view in self.node_views.values():
            if node_view.output is None:
                # Check if all dependencies are satisfied
                all_ready = all(
                    edge.source_view.output is not None
                    for edge in node_view.incoming_edges
                )
                if all_ready:
                    ready.append(node_view)
        return ready

    @cached_property
    def static_edges_list(self) -> List[Dict[str, Any]]:
        """Cached list of edge dictionaries for RuntimeContext."""
        return [
            {
                "id": ev.arrow.id,
                "source": ev.arrow.source,
                "target": ev.arrow.target,
                "sourceHandle": getattr(ev.arrow, "source_handle_id", ev.arrow.source),
                "targetHandle": getattr(ev.arrow, "target_handle_id", ev.arrow.target),
            }
            for ev in self.edge_views
        ]

    @cached_property
    def static_nodes_list(self) -> List[Dict[str, Any]]:
        """Cached list of node dictionaries for RuntimeContext."""
        return [
            {
                "id": nv.id,
                "type": nv.type,
                "data": nv.data,
            }
            for nv in self.node_views.values()
        ]
