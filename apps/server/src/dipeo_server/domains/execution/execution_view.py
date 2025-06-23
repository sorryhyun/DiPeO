"""Execution view that provides efficient access to DomainDiagram without modifying it."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable

from dipeo_domain.models import DomainDiagram, DomainNode, DomainArrow, DomainPerson, NodeOutput


@dataclass
class NodeView:
    """View of a node with pre-computed relationships."""
    node: DomainNode  # Original node, unchanged
    handler: Callable  # Direct handler reference
    
    # Pre-computed relationships
    incoming_edges: List['EdgeView'] = field(default_factory=list)
    outgoing_edges: List['EdgeView'] = field(default_factory=list)
    person: Optional[DomainPerson] = None  # Direct person reference for PersonJob
    
    # Runtime state (not modifying original)
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
        """Get incoming edges connected to specific handle."""
        return [e for e in self.incoming_edges if e.target_handle == handle]
    
    def get_input_values(self) -> Dict[str, Any]:
        """Collect all input values from completed sources."""
        inputs = {}
        for edge in self.incoming_edges:
            if edge.source_view.output:
                value = edge.source_view.output.outputs.get(edge.label, None)
                if value is not None:
                    inputs[edge.label] = value
        return inputs


@dataclass
class EdgeView:
    """View of an edge with direct node references."""
    arrow: DomainArrow  # Original arrow, unchanged
    source_view: NodeView  # Direct reference to source node view
    target_view: NodeView  # Direct reference to target node view
    
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
    """Execution-optimized view of DomainDiagram."""
    
    def __init__(self, diagram: DomainDiagram, handlers: Dict[str, Callable], api_keys: Dict[str, str]):
        self.diagram = diagram  # Keep original diagram
        self.handlers = handlers
        self.api_keys = api_keys
        
        # Build views
        self.node_views: Dict[str, NodeView] = {}
        self.edge_views: List[EdgeView] = []
        self.person_views: Dict[str, DomainPerson] = {}
        
        self._build_views()
        self.execution_order = self._compute_execution_order()
    
    def _build_views(self):
        """Build efficient views without modifying original data."""
        # Create person views
        if self.diagram.persons:
            self.person_views = {p.id: p for p in self.diagram.persons}
        
        # Create node views
        for node in self.diagram.nodes:
            handler = self._get_handler_for_type(node.type)
            node_view = NodeView(node=node, handler=handler)
            
            # Link person for PersonJob nodes
            if node.type == 'person_job' and node.data:
                person_id = node.data.get('personId')
                if person_id and person_id in self.person_views:
                    node_view.person = self.person_views[person_id]
            
            self.node_views[node.id] = node_view
        
        # Create edge views and link nodes
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
        """Get handler for node type with proper mapping."""
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
        """Compute topological execution order."""
        # Calculate in-degrees
        in_degree = {}
        for node_id, node_view in self.node_views.items():
            in_degree[node_id] = len(node_view.incoming_edges)
        
        # Find starting nodes
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
        """Get node view by ID."""
        return self.node_views.get(node_id)
    
    def get_ready_nodes(self) -> List[NodeView]:
        """Get nodes ready for execution."""
        ready = []
        for node_view in self.node_views.values():
            if node_view.output is None:  # Not yet executed
                # Check if all dependencies are complete
                all_ready = all(
                    edge.source_view.output is not None
                    for edge in node_view.incoming_edges
                )
                if all_ready:
                    ready.append(node_view)
        return ready
    
    def get_person_api_key(self, person_id: str) -> Optional[str]:
        """Get API key for a person."""
        person = self.person_views.get(person_id)
        if person and hasattr(person, 'api_key_id'):
            return self.api_keys.get(person.api_key_id)
        return None


# Usage in handlers becomes much cleaner:
async def efficient_person_job_handler(node_view: NodeView, ctx) -> NodeOutput:
    """Handler using the efficient view."""
    # Direct access to person
    person = node_view.person
    if not person:
        return NodeOutput(value={}, metadata={"error": "No person"})
    
    # Easy input collection
    inputs = node_view.get_input_values()
    
    # Check for first iteration inputs
    first_inputs = {}
    for edge in node_view.get_incoming_by_handle('first'):
        if edge.source_view.output:
            first_inputs[edge.label] = edge.source_view.output.outputs.get(edge.label)
    
    # Build prompt
    is_first = node_view.exec_count == 1
    if is_first and node_view.data.get('firstOnlyPrompt'):
        prompt = node_view.data['firstOnlyPrompt']
        for key, value in first_inputs.items():
            prompt = prompt.replace(f'{{{{{key}}}}}', str(value))
    else:
        prompt = node_view.data.get('defaultPrompt', '')
    
    # Continue with LLM call...
    return NodeOutput(value={'default': 'response'}, metadata={})