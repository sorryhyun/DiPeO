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

    incoming_edges: List['EdgeView'] = field(default_factory=list)
    outgoing_edges: List['EdgeView'] = field(default_factory=list)
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

    def get_incoming_by_handle(self, handle: str) -> List['EdgeView']:
        return [e for e in self.incoming_edges if e.target_handle == handle]

    def get_input_values(self) -> Dict[str, Any]:
        inputs = {}
        for edge in self.incoming_edges:
            if edge.source_view.output:
                value = edge.source_view.output.outputs.get(edge.label, None)
                if value is not None:
                    inputs[edge.label] = value
        return inputs


@dataclass
class EdgeView:
    arrow: DomainArrow
    source_view: NodeView
    target_view: NodeView

    @property
    def source_handle(self) -> str:
        parts = self.arrow.source.split(':', 1)
        return parts[1] if len(parts) > 1 else 'default'

    @property
    def target_handle(self) -> str:
        parts = self.arrow.target.split(':', 1)
        return parts[1] if len(parts) > 1 else 'default'

    @property
    def label(self) -> str:
        if self.arrow.data and isinstance(self.arrow.data, dict):
            return self.arrow.data.get('label', 'default')
        return 'default'

    @property
    def content_type(self) -> str:
        if self.arrow.data and isinstance(self.arrow.data, dict):
            return self.arrow.data.get('contentType', 'raw_text')
        return 'raw_text'


class ExecutionView:

    def __init__(self, diagram: DomainDiagram, handlers: Dict[str, Callable], api_keys: Dict[str, str]):
        self.diagram = diagram
        self.handlers = handlers
        self.api_keys = api_keys

        self.node_views: Dict[str, NodeView] = {}
        self.edge_views: List[EdgeView] = []
        self.person_views: Dict[str, DomainPerson] = {}

        self._build_views()
        self.execution_order = self._compute_execution_order()

    def _build_views(self):
        if self.diagram.persons:
            self.person_views = {p.id: p for p in self.diagram.persons}

        for node in self.diagram.nodes:
            handler = self._get_handler_for_type(node.type)
            node_view = NodeView(node=node, handler=handler)

            if node.type == 'person_job' and node.data:
                person_id = node.data.get('personId')
                if person_id and person_id in self.person_views:
                    node_view.person = self.person_views[person_id]

            self.node_views[node.id] = node_view

        for arrow in self.diagram.arrows:
            source_id = arrow.source.split(':')[0]
            target_id = arrow.target.split(':')[0]

            if source_id in self.node_views and target_id in self.node_views:
                edge_view = EdgeView(
                    arrow=arrow,
                    source_view=self.node_views[source_id],
                    target_view=self.node_views[target_id]
                )

                self.edge_views.append(edge_view)
                self.node_views[source_id].outgoing_edges.append(edge_view)
                self.node_views[target_id].incoming_edges.append(edge_view)

    def _get_handler_for_type(self, node_type: str) -> Optional[Callable]:
        type_map = {
            'start': 'Start',
            'person_job': 'PersonJob',
            'endpoint': 'Endpoint',
            'condition': 'Condition',
            'db': 'DB',
            'notion': 'Notion'
        }
        handler_name = type_map.get(node_type, node_type)
        return self.handlers.get(handler_name)

    def _compute_execution_order(self) -> List[List[NodeView]]:
        in_degree = {}
        for node_id, node_view in self.node_views.items():
            in_degree[node_id] = len(node_view.incoming_edges)

        queue = [nv for nid, nv in self.node_views.items() if in_degree[nid] == 0]
        levels = []

        while queue:
            current_level = queue[:]
            levels.append(current_level)
            next_queue = []

            for node_view in current_level:
                for edge in node_view.outgoing_edges:
                    target_id = edge.target_view.id
                    in_degree[target_id] -= 1
                    if in_degree[target_id] == 0:
                        next_queue.append(edge.target_view)

            queue = next_queue

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
        if person and hasattr(person, 'api_key_id'):
            return self.api_keys.get(person.api_key_id)
        return None
