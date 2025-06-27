"""Execution view for efficient access to DomainDiagram."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from dipeo_core import HandlerRegistry
from dipeo_domain.models import (
    DomainArrow,
    DomainDiagram,
    DomainNode,
    DomainPerson,
    NodeOutput,
)


@dataclass
class NodeView:
    node: DomainNode
    handler: Callable

    incoming_edges: list["EdgeView"] = field(default_factory=list)
    outgoing_edges: list["EdgeView"] = field(default_factory=list)
    person: DomainPerson | None = None

    output: NodeOutput | None = None
    exec_count: int = 0

    @property
    def id(self) -> str:
        return self.node.id

    @property
    def type(self) -> str:
        return self.node.type

    @property
    def data(self) -> dict[str, Any]:
        return self.node.data or {}

    def get_incoming_by_handle(self, handle: str) -> list["EdgeView"]:
        return [e for e in self.incoming_edges if e.target_handle == handle]

    def get_input_values(self) -> dict[str, Any]:
        inputs = {}
        for edge in self.incoming_edges:
            if edge.source_view.output:
                value = edge.source_view.output.value.get(edge.label, None)
                if value is not None:
                    inputs[edge.label] = value
        return inputs

    def get_active_inputs(self) -> dict[str, Any]:
        """Get inputs from edges that are active based on condition routing.

        This method filters inputs based on condition node routing decisions,
        returning only values from edges that match the condition result.
        """
        import logging

        log = logging.getLogger(__name__)

        inputs = {}

        # Split first/default once so we can reason about them together
        first_edges = []
        default_edges = []
        for edge in self.incoming_edges:
            if edge.source_view.output is None:
                continue
            (first_edges if edge.target_handle == "first" else default_edges).append(edge)

        selected_edges: list[EdgeView] = []
        if self.node.type == "person_job":
            has_first_payload = bool(first_edges)
            if self.exec_count == 1:
                # First execution
                selected_edges = first_edges if has_first_payload else default_edges
            else:
                # Second+ execution
                selected_edges = default_edges
        else:
            selected_edges = first_edges + default_edges

        for edge in selected_edges:

            # Check if this is from a condition node
            if edge.source_view.node.type == "condition":
                condition_result = edge.source_view.output.metadata.get(
                    "condition_result", False
                )
                edge_branch = (
                    edge.arrow.data.get("branch", None) if edge.arrow.data else None
                )

                # If edge has a branch specification, it must match the condition result
                if edge_branch is not None:
                    edge_branch_bool = edge_branch.lower() == "true"
                    if edge_branch_bool != condition_result:
                        log.debug(
                            f"Skipping edge from condition {edge.source_view.id} - "
                            f"branch {edge_branch} doesn't match result {condition_result}"
                        )
                        continue

            # Extract value based on label
            label = edge.label
            source_values = edge.source_view.output.value

            if label in source_values:
                inputs[label] = source_values[label]
            elif label == "default" and "conversation" in source_values:
                # Special case for conversation passthrough
                inputs[label] = source_values["conversation"]
            else:
                log.warning(
                    f"Edge label '{label}' not found in output from {edge.source_view.id} "
                    f"(available: {list(source_values.keys())})"
                )

        return inputs


@dataclass
class EdgeView:
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


class ExecutionView:
    def __init__(
        self,
        diagram: DomainDiagram,
        handler_registry: HandlerRegistry,
        api_keys: dict[str, str],
    ) -> None:
        self.diagram = diagram
        self.handler_registry = handler_registry
        self.api_keys = api_keys

        self.node_views: dict[str, NodeView] = {}
        self.edge_views: list[EdgeView] = []
        self.person_views: dict[str, DomainPerson] = {}

        self._build_views()
        self.execution_order = self._compute_execution_order()

    def _build_views(self) -> None:
        import logging

        logging.getLogger(__name__)

        if self.diagram.persons:
            self.person_views = {p.id: p for p in self.diagram.persons}

        for node in self.diagram.nodes:
            handler = self._get_handler_for_type(node.type)
            node_view = NodeView(node=node, handler=handler)

            if node.type == "person_job" and node.data:
                person_id = node.data.get("personId")
                if person_id and person_id in self.person_views:
                    node_view.person = self.person_views[person_id]

            self.node_views[node.id] = node_view

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

    def _get_handler_for_type(self, node_type: str) -> Callable | None:
        # Get handler from registry - the handler is already wrapped in NodeDefinition
        # We just need to return the handler function itself
        node_def = self.handler_registry.get(node_type)
        return node_def.handler if node_def else None

    def _compute_execution_order(self) -> list[list[NodeView]]:
        import logging

        log = logging.getLogger(__name__)

        in_degree = {}

        # Plain Kahn topological sort that counts all incoming edges
        for node_id, node_view in self.node_views.items():
            in_degree[node_id] = len(node_view.incoming_edges)

        queue = [nv for nid, nv in self.node_views.items() if in_degree[nid] == 0]
        levels = []

        while queue:
            current_level = queue[:]
            levels.append(current_level)
            log.info(f"Level {len(levels) - 1}: {[nv.id for nv in current_level]}")
            next_queue = []

            for node_view in current_level:
                for edge in node_view.outgoing_edges:
                    target_id = edge.target_view.id
                    in_degree[target_id] -= 1

                    if in_degree[target_id] == 0:
                        log.info(f"Adding {target_id} to next queue")
                        next_queue.append(edge.target_view)

            queue = next_queue

        # Log nodes that were never scheduled
        scheduled_nodes = set()
        for level in levels:
            for node in level:
                scheduled_nodes.add(node.id)

        for node_id in self.node_views:
            if node_id not in scheduled_nodes:
                log.warning(
                    f"Node {node_id} was never scheduled! In-degree: {in_degree[node_id]}"
                )

        return levels

    def get_node_view(self, node_id: str) -> NodeView | None:
        return self.node_views.get(node_id)

    def get_ready_nodes(self) -> list[NodeView]:
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

    def get_person_api_key(self, person_id: str) -> str | None:
        person = self.person_views.get(person_id)
        if person and hasattr(person, "api_key_id"):
            return self.api_keys.get(person.api_key_id)
        return None
