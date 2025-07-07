"""Simplified execution view for local execution."""

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Callable, Dict, List, Optional

from dipeo.models import DomainDiagram, NodeOutput, NodeType
from dipeo.models import DomainArrow, DomainNode, HandleLabel
from dipeo.models import parse_handle_id, HandleReference
from ..utils.input_resolution import get_active_inputs_simplified
from dipeo.domain.services.execution import InputResolutionService


@dataclass
class NodeView:
    """Node view with execution context."""

    node: DomainNode
    handler: Optional[Callable] = None
    incoming_edges: List["EdgeView"] = field(default_factory=list)
    outgoing_edges: List["EdgeView"] = field(default_factory=list)
    output: Optional[NodeOutput] = None
    exec_count: int = 0
    output_history: List[NodeOutput] = field(default_factory=list)
    input_resolution_service: Optional[InputResolutionService] = None
    execution_view: Optional["LocalExecutionView"] = None

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
        """Get inputs considering routing and person_job logic.
        
        Uses the simplified input resolution strategy for cleaner logic.
        """
        if self.input_resolution_service and self.execution_view:
            # Collect node outputs from execution view
            node_outputs = {}
            node_exec_counts = {}
            for node_id, node_view in self.execution_view.node_views.items():
                if node_view.output:
                    node_outputs[node_id] = node_view.output.model_dump()
                node_exec_counts[node_id] = node_view.exec_count
            
            # Extract memory config if available (for person_job nodes)
            node_memory_config = None
            if self.node.type == NodeType.person_job and hasattr(self.node, 'data'):
                node_data = self.node.data
                if isinstance(node_data, dict) and 'memory_config' in node_data:
                    node_memory_config = node_data['memory_config']
            
            # Use domain service to resolve inputs
            return self.input_resolution_service.resolve_inputs_for_node(
                node_id=self.node.id,
                node_type=self.node.type.value,
                diagram=self.execution_view.diagram,
                node_outputs=node_outputs,
                node_exec_counts=node_exec_counts,
                node_memory_config=node_memory_config
            )
        else:
            # Fallback to original implementation
            return get_active_inputs_simplified(self)


@dataclass
class EdgeView:
    """Edge view connecting two nodes."""

    arrow: DomainArrow
    source_view: NodeView
    target_view: NodeView
    source_handle_ref: Optional[HandleReference] = None
    target_handle_ref: Optional[HandleReference] = None

    @property
    def source_handle(self) -> str:
        if self.source_handle_ref and self.source_handle_ref.is_valid:
            return self.source_handle_ref.handle_label.value
        return HandleLabel.default.value

    @property
    def target_handle(self) -> str:
        if self.target_handle_ref and self.target_handle_ref.is_valid:
            return self.target_handle_ref.handle_label.value
        return HandleLabel.default.value

    @property
    def label(self) -> str:
        return self.arrow.label or HandleLabel.default.value

    @property
    def content_type(self) -> str:
        return self.arrow.content_type.value if self.arrow.content_type else "raw_text"


class LocalExecutionView:
    """Execution view for local execution."""

    def __init__(self, diagram: DomainDiagram, input_resolution_service: Optional[InputResolutionService] = None):
        self.diagram = diagram
        self.node_views: Dict[str, NodeView] = {}
        self.edge_views: List[EdgeView] = []
        self.input_resolution_service = input_resolution_service

        self._build_views()
        self.execution_order = self._compute_execution_order()

    def _build_views(self) -> None:
        """Build node and edge views from diagram."""
        for node in self.diagram.nodes:
            node_view = NodeView(
                node=node,
                input_resolution_service=self.input_resolution_service,
                execution_view=self
            )
            self.node_views[node.id] = node_view

        import logging

        log = logging.getLogger(__name__)
        
        # Clear handle cache at start of diagram loading
        HandleReference.clear_cache()
        
        for arrow in self.diagram.arrows:
            # Use cached handle references for performance
            source_ref = HandleReference.get_or_create(arrow.source)
            target_ref = HandleReference.get_or_create(arrow.target)
            
            if not source_ref.is_valid or not target_ref.is_valid:
                log.warning(f"Invalid handle format in arrow: {arrow.source} -> {arrow.target}")
                continue

            source_id = source_ref.node_id
            target_id = target_ref.node_id

            if source_id in self.node_views and target_id in self.node_views:
                edge_view = EdgeView(
                    arrow=arrow,
                    source_view=self.node_views[source_id],
                    target_view=self.node_views[target_id],
                    source_handle_ref=source_ref,
                    target_handle_ref=target_ref,
                )

                self.edge_views.append(edge_view)
                self.node_views[source_id].outgoing_edges.append(edge_view)
                self.node_views[target_id].incoming_edges.append(edge_view)


    def _compute_execution_order(self) -> List[List[NodeView]]:
        """Compute topological execution order using Kahn's algorithm."""
        import logging

        log = logging.getLogger(__name__)

        in_degree = {}
        for node_id, node_view in self.node_views.items():
            if node_view.node.type == NodeType.person_job.value:
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
                        target_view.node.type == NodeType.person_job.value
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