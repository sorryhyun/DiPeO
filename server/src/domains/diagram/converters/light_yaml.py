"""Light YAML format converter - uses labels instead of IDs."""
import yaml
from typing import Dict, Any, Optional, List
from .base import DiagramConverter
from ..models.domain import (
    DomainDiagram, DomainNode, DomainArrow, DomainHandle,
    DomainPerson, DomainApiKey, DiagramMetadata, Vec2,
    NodeType, HandleDirection, DataType, LLMService, ForgettingMode
)
import uuid


class LightYamlConverter(DiagramConverter):
    """Converts between DomainDiagram and light YAML format."""
    
    def serialize(self, diagram: DomainDiagram) -> str:
        """Convert domain diagram to light YAML."""
        # Create label mappings
        node_labels = {node_id: node.data.get('label', f'Node_{idx}') 
                      for idx, (node_id, node) in enumerate(diagram.nodes.items())}
        person_labels = {person_id: person.label 
                        for person_id, person in diagram.persons.items()}
        
        # Convert nodes with labels
        nodes = []
        for node_id, node in diagram.nodes.items():
            light_node = {
                'label': node_labels[node_id],
                'type': node.type.value,
                'position': {'x': node.position.x, 'y': node.position.y}
            }
            
            # Add person by label if assigned
            person_id = node.data.get('personId')
            if person_id and person_id in person_labels:
                light_node['person'] = person_labels[person_id]
            
            # Add props if present
            props = {k: v for k, v in node.data.items() 
                    if k not in ['label', 'personId']}
            if props:
                light_node['props'] = props
            
            nodes.append(light_node)
        
        # Convert arrows with label references
        connections = []
        for arrow in diagram.arrows.values():
            # Extract node IDs from handle IDs (format: "nodeId:handleName")
            source_node_id = arrow.source.split(':')[0]
            target_node_id = arrow.target.split(':')[0]
            
            source_label = node_labels.get(source_node_id, source_node_id)
            target_label = node_labels.get(target_node_id, target_node_id)
            
            light_arrow = {
                'from': source_label,
                'to': target_label
            }
            
            if arrow.data:
                light_arrow['data'] = arrow.data
            
            connections.append(light_arrow)
        
        # Convert persons
        persons = []
        for person in diagram.persons.values():
            light_person = {
                'label': person.label,
                'service': person.service.value,
                'model': person.model
            }
            
            if person.systemPrompt:
                light_person['systemPrompt'] = person.systemPrompt
            
            if person.forgettingMode != ForgettingMode.NONE:
                light_person['forgettingMode'] = person.forgettingMode.value
            
            persons.append(light_person)
        
        # Build light format
        data = {
            'version': 'light',
            'nodes': nodes,
            'connections': connections
        }
        
        if persons:
            data['persons'] = persons
        
        # Add metadata if present
        if diagram.metadata and diagram.metadata.name:
            data['name'] = diagram.metadata.name
        if diagram.metadata and diagram.metadata.description:
            data['description'] = diagram.metadata.description
        
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def deserialize(self, content: str) -> DomainDiagram:
        """Convert light YAML to domain diagram."""
        data = yaml.safe_load(content)
        
        if not isinstance(data, dict):
            raise ValueError("Invalid YAML: expected a dictionary at root level")
        
        diagram = DomainDiagram(
            nodes={},
            arrows={},
            handles={},
            persons={},
            api_keys={}
        )
        
        # Create metadata
        diagram.metadata = DiagramMetadata(
            name=data.get('name', 'Imported Diagram'),
            description=data.get('description', ''),
            version='2.0.0'
        )
        
        # Create mappings
        label_to_node_id = {}
        person_label_to_id = {}
        
        # Convert persons first
        for person_data in data.get('persons', []):
            person_id = f"person_{uuid.uuid4().hex[:8]}"
            person_label_to_id[person_data['label']] = person_id
            
            # Create a default API key for the person
            api_key_id = f"apikey_{uuid.uuid4().hex[:8]}"
            diagram.api_keys[api_key_id] = DomainApiKey(
                id=api_key_id,
                label=f"{person_data['label']}_key",
                service=LLMService(person_data['service']),
                key="YOUR_API_KEY_HERE"  # Placeholder
            )
            
            diagram.persons[person_id] = DomainPerson(
                id=person_id,
                label=person_data['label'],
                service=LLMService(person_data['service']),
                model=person_data['model'],
                systemPrompt=person_data.get('systemPrompt'),
                api_key_id=api_key_id,
                forgettingMode=ForgettingMode(person_data.get('forgettingMode', 'none'))
            )
        
        # Convert nodes
        for idx, node_data in enumerate(data.get('nodes', [])):
            node_id = f"{node_data['type']}_{uuid.uuid4().hex[:8]}"
            label = node_data.get('label', f"Node_{idx}")
            label_to_node_id[label] = node_id
            
            # Build node data
            node_data_dict = {'label': label}
            
            # Assign person if specified
            if 'person' in node_data and node_data['person'] in person_label_to_id:
                node_data_dict['personId'] = person_label_to_id[node_data['person']]
            
            # Add props
            if 'props' in node_data:
                node_data_dict.update(node_data['props'])
            
            pos = node_data.get('position', {'x': 100 + idx * 200, 'y': 100})
            diagram.nodes[node_id] = DomainNode(
                id=node_id,
                type=NodeType(node_data['type']),
                position=Vec2(x=pos['x'], y=pos['y']),
                data=node_data_dict
            )
            
            # Auto-generate handles based on node type
            self._generate_handles_for_node(diagram, node_id, node_data['type'])
        
        # Convert connections to arrows
        for idx, conn in enumerate(data.get('connections', [])):
            source_id = label_to_node_id.get(conn['from'])
            target_id = label_to_node_id.get(conn['to'])
            
            if source_id and target_id:
                arrow_id = f"arrow_{uuid.uuid4().hex[:8]}"
                # Use default handles
                source_handle = f"{source_id}:output"
                target_handle = f"{target_id}:input"
                
                diagram.arrows[arrow_id] = DomainArrow(
                    id=arrow_id,
                    source=source_handle,
                    target=target_handle,
                    data=conn.get('data', {})
                )
        
        return diagram
    
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
        """Detect if content is light YAML format."""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return 0.0
            
            score = 0.0
            
            # Check for light format indicators
            if data.get('version') == 'light':
                score += 0.4
            if 'nodes' in data and isinstance(data['nodes'], list):
                score += 0.3
                # Check if nodes use labels
                if any('label' in node for node in data['nodes']):
                    score += 0.1
            if 'connections' in data and isinstance(data['connections'], list):
                score += 0.2
                # Check if connections use from/to
                if any('from' in conn and 'to' in conn for conn in data['connections']):
                    score += 0.1
            
            return min(score, 1.0)
        except:
            return 0.0