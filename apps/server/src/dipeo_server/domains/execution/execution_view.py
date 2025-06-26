"""Execution view for efficient access to DomainDiagram."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

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

    incoming_edges: List["EdgeView"] = field(default_factory=list)
    outgoing_edges: List["EdgeView"] = field(default_factory=list)
    person: Optional[DomainPerson] = None

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

    def get_incoming_by_handle(self, handle: str) -> List["EdgeView"]:
        return [e for e in self.incoming_edges if e.target_handle == handle]

    def get_input_values(self) -> Dict[str, Any]:
        inputs = {}
        for edge in self.incoming_edges:
            if edge.source_view.output:
                value = edge.source_view.output.value.get(edge.label, None)
                if value is not None:
                    inputs[edge.label] = value
        return inputs

    def get_active_inputs(self) -> Dict[str, Any]:
        """Get inputs from edges that are active based on condition routing.
        
        This method filters inputs based on condition node routing decisions,
        returning only values from edges that match the condition result.
        """
        import logging
        log = logging.getLogger(__name__)
        
        inputs = {}
        
        for edge in self.incoming_edges:
            # Skip edges from nodes that have no output
            if not edge.source_view.output:
                log.debug(f"Skipping edge from {edge.source_view.id} - no output")
                continue
            
            # Check if this is from a condition node
            if edge.source_view.node.type == "condition":
                condition_result = edge.source_view.output.metadata.get("condition_result", False)
                edge_branch = edge.arrow.data.get("branch", None) if edge.arrow.data else None
                
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
        handlers: Dict[str, Callable],
        api_keys: Dict[str, str],
    ) -> None:
        self.diagram = diagram
        self.handlers = handlers
        self.api_keys = api_keys

        self.node_views: Dict[str, NodeView] = {}
        self.edge_views: List[EdgeView] = []
        self.person_views: Dict[str, DomainPerson] = {}

        self._build_views()
        self.execution_order = self._compute_execution_order()

    def _build_views(self) -> None:
        import logging

        log = logging.getLogger(__name__)

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

    def _get_handler_for_type(self, node_type: str) -> Optional[Callable]:
        # Handlers now use lowercase names matching the node types
        return self.handlers.get(node_type)

    def _compute_execution_order(self) -> List[List[NodeView]]:
        import logging

        log = logging.getLogger(__name__)

        in_degree = {}
        # Track person_job nodes that have :first connections
        person_job_first_sources = {}  # node_id -> source_node_id

        for node_id, node_view in self.node_views.items():
            # For person_job nodes with a "first" handle, we only count non-"first" edges
            # This allows them to start when they receive their initial input
            if node_view.node.type == "person_job":
                # Count only edges that don't go to the "first" handle
                non_first_edges = [
                    e for e in node_view.incoming_edges if e.target_handle != "first"
                ]
                in_degree[node_id] = len(non_first_edges)

                # Track the source of :first connections
                first_edges = [
                    e for e in node_view.incoming_edges if e.target_handle == "first"
                ]
                if first_edges:
                    # Store the source node ID
                    person_job_first_sources[node_id] = first_edges[0].source_view.id
            else:
                in_degree[node_id] = len(node_view.incoming_edges)

        # Find person_job nodes that share the same :first source
        source_to_nodes = {}
        for node_id, source_id in person_job_first_sources.items():
            if source_id not in source_to_nodes:
                source_to_nodes[source_id] = []
            source_to_nodes[source_id].append(node_id)

        # For nodes sharing the same :first source, check if they have dependencies between them
        # If they do, we need to respect that ordering by adjusting in_degree
        for source_id, node_ids in source_to_nodes.items():
            if len(node_ids) > 1:
                log.info(f"Nodes {node_ids} share :first source {source_id}")
                # Check for dependencies between these nodes
                for i, node_id in enumerate(node_ids):
                    node_view = self.node_views[node_id]
                    # Check if this node has edges to other nodes in the same group
                    for edge in node_view.outgoing_edges:
                        if (
                            edge.target_view.id in node_ids
                            and edge.target_handle != "first"
                        ):
                            # This creates a dependency - increase target's in_degree
                            log.info(
                                f"Found dependency: {node_id} -> {edge.target_view.id}"
                            )
                            in_degree[edge.target_view.id] += 1

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
                    # Only reduce in_degree if this edge was counted initially
                    # (i.e., skip edges to "first" handles of person_job nodes)
                    if (
                        edge.target_view.node.type == "person_job"
                        and edge.target_handle == "first"
                    ):
                        log.info(
                            f"Skipping in_degree reduction for edge to first handle of person_job {target_id}"
                        )
                    else:
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

    def get_node_view(self, node_id: str) -> Optional[NodeView]:
        return self.node_views.get(node_id)

    def get_ready_nodes(self) -> List[NodeView]:
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

    def get_person_api_key(self, person_id: str) -> Optional[str]:
        person = self.person_views.get(person_id)
        if person and hasattr(person, "api_key_id"):
            return self.api_keys.get(person.api_key_id)
        return None
