"""Readable YAML format converter - refactored to use enhanced base and shared components."""
import uuid
from typing import Dict, Any, List, Set, Optional

from .base import YamlBasedConverter
from ..models.domain import (
    DomainDiagram, DomainNode, DomainArrow, DomainPerson,
    DomainApiKey, DiagramMetadata, Vec2,
    NodeType, LLMService, ForgettingMode
)


class ReadableYamlConverter(YamlBasedConverter):
    """Converts between DomainDiagram and readable workflow format using shared components."""
    
    def __init__(self):
        super().__init__()
        self.agent_map = {}
        self.step_to_node_id = {}
        self.prev_node_id = None
    
    # Implement abstract methods from EnhancedDiagramConverter
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract node data from workflow steps."""
        return data.get('workflow', [])
    
    def extract_arrows(self, data: Dict[str, Any], diagram: DomainDiagram) -> List[Dict[str, Any]]:
        """Extract edges by connecting sequential workflow steps."""
        edges = []
        workflow_steps = data.get('workflow', [])
        
        for idx, step in enumerate(workflow_steps):
            node_id = self.step_to_node_id.get(idx)
            if not node_id:
                continue
            
            # Connect to previous node if exists
            if self.prev_node_id and node_id != self.prev_node_id:
                source_handle = f"{self.prev_node_id}:output"
                target_handle = f"{node_id}:input"
                edge_id, _, _ = self.arrow_builder.create_simple_arrow(
                    self.prev_node_id, node_id
                )
                edges.append({
                    'id': edge_id,
                    'source': source_handle,
                    'target': target_handle
                })
            
            # Handle conditional branches
            if 'branches' in step:
                for branch_name, branch_steps in step['branches'].items():
                    if branch_steps:
                        # Create edges for branches (simplified)
                        branch_handle = f"{node_id}:{branch_name}"
                        # This would need more logic for proper branch handling
            
            self.prev_node_id = node_id
        
        return edges
    
    def extract_node_id(self, node_data: Dict[str, Any], index: int) -> str:
        """Generate node ID and track mapping."""
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        self.step_to_node_id[index] = node_id
        return node_id
    
    def extract_node_type(self, node_data: Dict[str, Any]) -> str:
        """Determine node type from step data."""
        # Check if it's the first step
        is_first = len(self.step_to_node_id) == 0
        node_type = self.node_mapper.determine_node_type(node_data, is_first)
        return node_type.value
    
    def extract_node_properties(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract node properties from workflow step."""
        properties = {
            'label': node_data.get('name', node_data.get('step', f'Step {len(self.step_to_node_id) + 1}'))
        }
        
        # Assign agent/person
        if 'agent' in node_data and node_data['agent'] in self.agent_map:
            properties['personId'] = self.agent_map[node_data['agent']]
        
        # Add task-specific data
        task_fields = ['task', 'input', 'action', 'condition', 'code', 'language', 
                      'variable', 'value', 'expression', 'database_id', 'prompt']
        for field in task_fields:
            if field in node_data:
                properties[field] = node_data[field]
        
        return properties
    
    def post_process_diagram(self, diagram: DomainDiagram, data: Dict[str, Any]) -> None:
        """Process agents and create metadata."""
        # Process agents first
        self._process_agents(diagram, data)
        
        # Set metadata
        diagram.metadata = DiagramMetadata(
            name=data.get('name', 'Imported Workflow'),
            description=data.get('description', ''),
            version='2.0.0'
        )
        
        # Convert edges to arrows for compatibility
        diagram.arrows = {}
        for edge in diagram.edges.values():
            arrow = DomainArrow(
                id=edge.id,
                source=edge.source,
                target=edge.target,
                data={}
            )
            diagram.arrows[arrow.id] = arrow
        diagram.edges = {}
        
        # Clear temporary state
        self.agent_map.clear()
        self.step_to_node_id.clear()
        self.prev_node_id = None
    
    def _process_agents(self, diagram: DomainDiagram, data: Dict[str, Any]) -> None:
        """Process agents from readable YAML data."""
        diagram.persons = {}
        diagram.api_keys = {}
        
        for agent in data.get('agents', []):
            person_id = f"person_{uuid.uuid4().hex[:8]}"
            
            # Parse LLM string (format: "service/model")
            llm_parts = agent['llm'].split('/', 1)
            service = llm_parts[0]
            model = llm_parts[1] if len(llm_parts) > 1 else 'default'
            
            # Create API key
            api_key_id = f"apikey_{uuid.uuid4().hex[:8]}"
            diagram.api_keys[api_key_id] = DomainApiKey(
                id=api_key_id,
                label=f"{agent['name']}_key",
                service=LLMService(service),
                key="YOUR_API_KEY_HERE"
            )
            
            diagram.persons[person_id] = DomainPerson(
                id=person_id,
                label=agent['name'],
                service=LLMService(service),
                model=model,
                systemPrompt=agent.get('prompt'),
                api_key_id=api_key_id,
                forgettingMode=ForgettingMode(agent.get('memory', 'none'))
            )
            self.agent_map[agent['name']] = person_id
    
    def _calculate_format_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence that this is readable YAML format."""
        confidence = 0.0
        
        # Check for workflow structure
        if 'workflow' in data and isinstance(data['workflow'], list):
            confidence += 0.4
            
            # Check if steps have expected fields
            if data['workflow']:
                step = data['workflow'][0]
                if any(field in step for field in ['step', 'name', 'task', 'agent']):
                    confidence += 0.3
        
        # Check for agents section
        if 'agents' in data and isinstance(data['agents'], list):
            confidence += 0.2
            if data['agents'] and all('llm' in agent for agent in data['agents'][:2]):
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    # Serialization methods
    def diagram_to_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        """Convert diagram to readable YAML data structure."""
        workflow = {
            'name': diagram.metadata.name if diagram.metadata else 'Unnamed Workflow',
            'description': diagram.metadata.description if diagram.metadata else ''
        }
        
        # Add agents section
        if diagram.persons:
            workflow['agents'] = []
            for person in diagram.persons.values():
                agent = {
                    'name': person.label,
                    'llm': f"{person.service.value}/{person.model}"
                }
                if person.systemPrompt:
                    agent['prompt'] = person.systemPrompt
                if person.forgettingMode != ForgettingMode.NONE:
                    agent['memory'] = person.forgettingMode.value
                workflow['agents'].append(agent)
        
        # Build workflow steps
        workflow['workflow'] = []
        processed = set()
        
        # Find start nodes
        start_nodes = [n for n in diagram.nodes.values() if n.type == NodeType.START]
        if not start_nodes:
            # If no start node, begin with nodes that have no incoming connections
            arrows = diagram.arrows if diagram.arrows else diagram.edges
            incoming_nodes = {arrow.target.split(':')[0] for arrow in arrows.values()}
            start_nodes = [n for n in diagram.nodes.values() if n.id not in incoming_nodes]
        
        # Process each flow
        for start_node in start_nodes:
            flow_steps = self._build_flow_steps(start_node, diagram, processed)
            workflow['workflow'].extend(flow_steps)
        
        # Add any unprocessed nodes
        for node_id, node in diagram.nodes.items():
            if node_id not in processed:
                workflow['workflow'].append(self._node_to_step(node, diagram))
                processed.add(node_id)
        
        return workflow
    
    def _build_flow_steps(self, node: DomainNode, diagram: DomainDiagram, 
                         processed: Set[str]) -> List[Dict[str, Any]]:
        """Build workflow steps from a node flow."""
        steps = []
        current = node
        
        while current and current.id not in processed:
            steps.append(self._node_to_step(current, diagram))
            processed.add(current.id)
            
            # Find next node
            arrows = diagram.arrows if diagram.arrows else diagram.edges
            next_arrows = [a for a in arrows.values() 
                          if a.source.startswith(f"{current.id}:")]
            
            if next_arrows:
                # Follow the first arrow (simplified)
                next_node_id = next_arrows[0].target.split(':')[0]
                current = diagram.nodes.get(next_node_id)
            else:
                current = None
        
        return steps
    
    def _node_to_step(self, node: DomainNode, diagram: DomainDiagram) -> Dict[str, Any]:
        """Convert a node to a workflow step."""
        step = {}
        
        # Add name/label
        if 'label' in node.data:
            step['name'] = node.data['label']
        
        # Add agent if assigned
        person_id = node.data.get('personId')
        if person_id and person_id in diagram.persons:
            step['agent'] = diagram.persons[person_id].label
        
        # Add type-specific fields
        if node.type == NodeType.START:
            if 'input' in node.data:
                step['input'] = node.data['input']
        elif node.type == NodeType.PERSON_JOB:
            if 'task' in node.data:
                step['task'] = node.data['task']
            elif 'prompt' in node.data:
                step['task'] = node.data['prompt']
        elif node.type == NodeType.CONDITION:
            if 'condition' in node.data:
                step['condition'] = node.data['condition']
            elif 'expression' in node.data:
                step['condition'] = node.data['expression']
        # Add other node type conversions as needed
        
        return step