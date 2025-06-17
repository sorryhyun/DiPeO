"""Readable YAML format converter - human-friendly workflow format."""
import yaml
from typing import Dict, Any, List, Set
from .base import DiagramConverter
from ..models.domain import (
    DomainDiagram, DomainNode, DomainArrow, DomainHandle,
    DomainPerson, DomainApiKey, DiagramMetadata, Vec2,
    NodeType, HandleDirection, DataType, LLMService, ForgettingMode
)
import uuid


class ReadableYamlConverter(DiagramConverter):
    """Converts between DomainDiagram and readable workflow format."""
    
    def serialize(self, diagram: DomainDiagram) -> str:
        """Convert domain diagram to readable YAML."""
        # Build workflow structure
        workflow = {
            'name': diagram.metadata.name if diagram.metadata else 'Unnamed Workflow',
            'description': diagram.metadata.description if diagram.metadata else ''
        }
        
        # Add agents section if any
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
        
        # Track processed nodes
        processed = set()
        
        # Find start nodes
        start_nodes = [n for n in diagram.nodes.values() if n.type == NodeType.START]
        if not start_nodes:
            # If no start node, begin with nodes that have no incoming connections
            incoming_nodes = {arrow.target.split(':')[0] for arrow in diagram.arrows.values()}
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
        
        return yaml.dump(workflow, default_flow_style=False, sort_keys=False, 
                        allow_unicode=True, width=80)
    
    def deserialize(self, content: str) -> DomainDiagram:
        """Convert readable YAML to domain diagram."""
        data = yaml.safe_load(content)
        
        if not isinstance(data, dict):
            raise ValueError("Invalid YAML: expected a dictionary at root level")
        
        diagram = DomainDiagram(
            nodes={},
            arrows={},
            handles={},
            persons={},
            api_keys={},
            metadata=DiagramMetadata(
                name=data.get('name', 'Imported Workflow'),
                description=data.get('description', ''),
                version='2.0.0'
            )
        )
        
        # Convert agents to persons
        agent_map = {}
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
            agent_map[agent['name']] = person_id
        
        # Convert workflow steps to nodes
        prev_node_id = None
        step_to_node_id = {}
        
        for idx, step in enumerate(data.get('workflow', [])):
            node_id = f"node_{uuid.uuid4().hex[:8]}"
            
            # Determine node type from step
            node_type = self._determine_node_type(step, idx == 0)
            
            # Build node data
            node_data = {
                'label': step.get('name', step.get('step', f'Step {idx + 1}'))
            }
            
            # Assign agent/person
            if 'agent' in step and step['agent'] in agent_map:
                node_data['personId'] = agent_map[step['agent']]
            
            # Add task-specific data
            if 'task' in step:
                node_data['task'] = step['task']
            if 'input' in step:
                node_data['input'] = step['input']
            if 'action' in step:
                node_data['action'] = step['action']
            if 'condition' in step:
                node_data['condition'] = step['condition']
            if 'code' in step:
                node_data['code'] = step['code']
            if 'language' in step:
                node_data['language'] = step['language']
            
            # Create node
            position = self._calculate_position(idx)
            diagram.nodes[node_id] = DomainNode(
                id=node_id,
                type=node_type,
                position=position,
                data=node_data
            )
            
            # Store mapping for connections
            step_name = step.get('name', step.get('step', f'Step {idx + 1}'))
            step_to_node_id[step_name] = node_id
            
            # Generate handles
            self._generate_handles_for_node(diagram, node_id, node_type.value)
            
            # Create arrow from previous node (linear flow)
            if prev_node_id and 'connects_to' not in step:
                arrow_id = f"arrow_{uuid.uuid4().hex[:8]}"
                diagram.arrows[arrow_id] = DomainArrow(
                    id=arrow_id,
                    source=f"{prev_node_id}:output",
                    target=f"{node_id}:input",
                    data={}
                )
            
            # Handle explicit connections
            if 'connects_to' in step:
                connections = step['connects_to'] if isinstance(step['connects_to'], list) else [step['connects_to']]
                for target_name in connections:
                    if target_name in step_to_node_id:
                        arrow_id = f"arrow_{uuid.uuid4().hex[:8]}"
                        target_id = step_to_node_id[target_name]
                        
                        # Determine source handle based on condition
                        source_handle = f"{node_id}:output"
                        if node_type == NodeType.CONDITION:
                            # Try to infer true/false from context
                            source_handle = f"{node_id}:true"  # Default to true
                        
                        diagram.arrows[arrow_id] = DomainArrow(
                            id=arrow_id,
                            source=source_handle,
                            target=f"{target_id}:input",
                            data={}
                        )
            
            prev_node_id = node_id
        
        return diagram
    
    def _build_flow_steps(self, start_node: DomainNode, diagram: DomainDiagram, 
                         processed: Set[str]) -> List[Dict[str, Any]]:
        """Build workflow steps following the flow."""
        steps = []
        current = start_node
        
        while current and current.id not in processed:
            processed.add(current.id)
            steps.append(self._node_to_step(current, diagram))
            
            # Find next node(s)
            next_nodes = []
            for arrow in diagram.arrows.values():
                if arrow.source.startswith(current.id + ':'):
                    target_node_id = arrow.target.split(':')[0]
                    if target_node_id in diagram.nodes:
                        next_nodes.append(diagram.nodes[target_node_id])
            
            # For simplicity, follow the first connection
            current = next_nodes[0] if next_nodes else None
        
        return steps
    
    def _node_to_step(self, node: DomainNode, diagram: DomainDiagram) -> Dict[str, Any]:
        """Convert a node to a workflow step."""
        step = {
            'step': node.data.get('label', node.type.value),
            'type': node.type.value
        }
        
        # Add agent if assigned
        person_id = node.data.get('personId')
        if person_id and person_id in diagram.persons:
            person = diagram.persons[person_id]
            step['agent'] = person.label
        
        # Add node-specific data
        if node.type == NodeType.PERSON_JOB:
            if 'task' in node.data:
                step['task'] = node.data['task']
            elif 'input' in node.data:
                step['task'] = node.data['input']
        
        elif node.type == NodeType.CONDITION:
            step['condition'] = node.data.get('condition', 'true')
        
        elif node.type == NodeType.JOB:
            step['code'] = node.data.get('code', '')
            step['language'] = node.data.get('language', 'python')
        
        elif node.type == NodeType.START:
            if 'input' in node.data:
                step['input'] = node.data['input']
        
        # Add connections if non-linear
        connections = []
        for arrow in diagram.arrows.values():
            if arrow.source.startswith(node.id + ':'):
                target_node_id = arrow.target.split(':')[0]
                if target_node_id in diagram.nodes:
                    target_node = diagram.nodes[target_node_id]
                    connections.append(target_node.data.get('label', target_node_id))
        
        if len(connections) > 1 or (len(connections) == 1 and node.type == NodeType.CONDITION):
            step['connects_to'] = connections
        
        return step
    
    def _determine_node_type(self, step: Dict[str, Any], is_first: bool) -> NodeType:
        """Determine node type from step data."""
        step_type = step.get('type')
        
        if step_type:
            return NodeType(step_type)
        
        # Infer from content
        if is_first and 'input' in step:
            return NodeType.START
        elif 'condition' in step:
            return NodeType.CONDITION
        elif 'code' in step:
            return NodeType.JOB
        elif 'agent' in step or 'task' in step:
            return NodeType.PERSON_JOB
        elif 'output' in step:
            return NodeType.ENDPOINT
        else:
            return NodeType.PERSON_JOB  # Default
    
    def _calculate_position(self, index: int) -> Vec2:
        """Calculate node position based on index."""
        # Simple grid layout
        columns = 4
        row = index // columns
        col = index % columns
        
        return Vec2(
            x=100 + col * 250,
            y=100 + row * 150
        )
    
    def _generate_handles_for_node(self, diagram: DomainDiagram, node_id: str, node_type: str):
        """Generate default handles for a node based on its type."""
        # Input handle (except for start nodes)
        if node_type != 'start':
            input_handle_id = f"{node_id}:input"
            diagram.handles[input_handle_id] = DomainHandle(
                id=input_handle_id,
                nodeId=node_id,
                label="input",
                direction=HandleDirection.INPUT,
                dataType=DataType.ANY,
                position="left"
            )
        
        # Output handle (except for endpoint nodes)
        if node_type != 'endpoint':
            output_handle_id = f"{node_id}:output"
            diagram.handles[output_handle_id] = DomainHandle(
                id=output_handle_id,
                nodeId=node_id,
                label="output",
                direction=HandleDirection.OUTPUT,
                dataType=DataType.ANY,
                position="right"
            )
        
        # Additional handles for condition nodes
        if node_type == 'condition':
            true_handle_id = f"{node_id}:true"
            false_handle_id = f"{node_id}:false"
            
            diagram.handles[true_handle_id] = DomainHandle(
                id=true_handle_id,
                nodeId=node_id,
                label="true",
                direction=HandleDirection.OUTPUT,
                dataType=DataType.BOOLEAN,
                position="right"
            )
            
            diagram.handles[false_handle_id] = DomainHandle(
                id=false_handle_id,
                nodeId=node_id,
                label="false",
                direction=HandleDirection.OUTPUT,
                dataType=DataType.BOOLEAN,
                position="right"
            )
    
    def detect_format_confidence(self, content: str) -> float:
        """Detect if content is readable YAML format."""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return 0.0
            
            score = 0.0
            
            # Check for readable format indicators
            if 'workflow' in data and isinstance(data['workflow'], list):
                score += 0.4
            if 'agents' in data and isinstance(data['agents'], list):
                score += 0.2
            if 'name' in data:
                score += 0.1
            if 'description' in data:
                score += 0.1
            
            # Check workflow step structure
            if 'workflow' in data:
                steps = data['workflow']
                if any('step' in s or 'task' in s for s in steps):
                    score += 0.2
            
            return min(score, 1.0)
        except:
            return 0.0