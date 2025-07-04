"""Simplified execution view for local execution."""

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional

from dipeo_domain.models import DomainArrow, DomainDiagram, DomainNode, NodeOutput


@dataclass
class NodeView:
    """Node view with execution context."""

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
        """Get inputs considering routing and person_job logic."""
        import logging

        log = logging.getLogger(__name__)

        inputs = {}

        first_edges = []
        default_edges = []

        for edge in self.incoming_edges:
            if edge.source_view.output is None:
                continue

            if edge.target_handle == "first":
                first_edges.append(edge)
            else:
                default_edges.append(edge)

        if self.node.type == "person_job":
            if self.exec_count == 0 and first_edges:
                selected_edges = first_edges
            else:
                selected_edges = default_edges
        else:
            selected_edges = first_edges + default_edges

        for edge in selected_edges:
            if edge.source_view.node.type == "condition":
                condition_result = edge.source_view.output.metadata.get(
                    "condition_result", False
                )
                edge_branch = edge.arrow.data.get("branch") if edge.arrow.data else None

                if edge_branch is not None:
                    edge_branch_bool = edge_branch.lower() == "true"
                    if edge_branch_bool != condition_result:
                        continue

            label = edge.label
            source_values = edge.source_view.output.value

            # Process edge from source

            value = None
            # Special handling for condition nodes - use source handle to select branch
            if edge.source_view.node.type == "condition":
                # For condition nodes, use the source handle (True/False) to select the value
                source_handle = edge.source_handle
                if source_handle in source_values:
                    value = source_values[source_handle]
                    pass  # Using branch value from condition node
            # Special handling for conversation_state edges
            elif edge.content_type == "conversation_state" and "conversation" in source_values:
                value = source_values["conversation"]
                pass  # Using conversation value for conversation_state edge
            elif label in source_values:
                value = source_values[label]
                pass  # Found exact match for label
            elif "default" in source_values:
                value = source_values["default"]
                pass  # Using default value
            elif "conversation" in source_values:
                value = source_values["conversation"]
                pass  # Using conversation value
            elif len(source_values) == 1:
                value = list(source_values.values())[0]
                pass  # Using only available value
            else:
                pass  # No suitable value found
            if value is not None:
                inputs[label] = value

        # Return final inputs
        return inputs


@dataclass
class EdgeView:
    """Edge view connecting two nodes."""

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
        return self.arrow.label or "default"

    @property
    def content_type(self) -> str:
        return self.arrow.content_type.value if self.arrow.content_type else "raw_text"


class LocalExecutionView:
    """Execution view for local execution."""

    def __init__(self, diagram: DomainDiagram):
        self.diagram = diagram
        self.node_views: Dict[str, NodeView] = {}
        self.edge_views: List[EdgeView] = []

        self._build_views()
        self.execution_order = self._compute_execution_order()

    def _build_views(self) -> None:
        """Build node and edge views from diagram."""
        for node in self.diagram.nodes:
            node_view = NodeView(node=node)
            self.node_views[node.id] = node_view

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
                pass

    def _compute_execution_order(self) -> List[List[NodeView]]:
        """Compute topological execution order using Kahn's algorithm."""
        import logging

        log = logging.getLogger(__name__)

        in_degree = {}
        for node_id, node_view in self.node_views.items():
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

        queue = [nv for nid, nv in self.node_views.items() if in_degree[nid] == 0]
        levels = []
        processed = set()

        while queue:
            current_level = queue[:]
            levels.append(current_level)
            next_queue = []

            for node_view in current_level:
                processed.add(node_view.id)
                for edge in node_view.outgoing_edges:
                    target_id = edge.target_view.id
                    target_view = edge.target_view

                    should_decrement = True
                    if (
                        target_view.node.type == "person_job"
                        and edge.target_handle != "first"
                    ):
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

        unprocessed = set(self.node_views.keys()) - processed
        if unprocessed:
            log.warning(f"Nodes not included in execution order: {unprocessed}")

        return levels

    def get_node_view(self, node_id: str) -> Optional[NodeView]:
        """Get node view by ID."""
        return self.node_views.get(node_id)

    def get_ready_nodes(self) -> List[NodeView]:
        """Get nodes ready to execute."""
        ready = []
        for node_view in self.node_views.values():
            if node_view.output is None:
                all_ready = all(
                    edge.source_view.output is not None
                    for edge in node_view.incoming_edges
                )
                if all_ready:
                    ready.append(node_view)
        return ready

    @cached_property
    def static_edges_list(self) -> List[Dict[str, Any]]:
        """Cached edge list for RuntimeContext."""
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
        """Cached node list for RuntimeContext."""
        return [
            {
                "id": nv.id,
                "type": nv.type,
                "data": nv.data,
            }
            for nv in self.node_views.values()
        ]
