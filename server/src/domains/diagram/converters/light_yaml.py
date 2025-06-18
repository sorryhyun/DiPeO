"""Light YAML format converter - refactored to use enhanced base and shared components."""
import uuid
from typing import Dict, Any, List, Optional

from .base import YamlBasedConverter
from ..models.domain import (
    DomainDiagram, DomainNode, DomainArrow, DomainPerson, 
    DomainApiKey, DiagramMetadata, Vec2,
    NodeType, LLMService, ForgettingMode
)


class LightYamlConverter(YamlBasedConverter):
    """Converts between DomainDiagram and light YAML format using shared components."""
    
    def __init__(self):
        super().__init__()
        self.label_to_node_id = {}
        self.node_id_to_label = {}
        self.person_label_to_id = {}
        self.person_id_to_label = {}
    
    # Implement abstract methods from EnhancedDiagramConverter
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract node data from light YAML format."""
        return data.get('nodes', [])
    
    def extract_arrows(self, data: Dict[str, Any], diagram: DomainDiagram) -> List[Dict[str, Any]]:
        """Extract edge data from light YAML format connections."""
        edges = []
        for conn in data.get('connections', []):
            source_id = self.label_to_node_id.get(conn['from'])
            target_id = self.label_to_node_id.get(conn['to'])
            
            if source_id and target_id:
                # Use default handles
                source_handle = f"{source_id}:output"
                target_handle = f"{target_id}:input"
                
                edges.append({
                    'id': f"arrow_{uuid.uuid4().hex[:8]}",
                    'source': source_handle,
                    'target': target_handle,
                    'data': conn.get('data', {})
                })
        
        return edges
    
    def extract_node_id(self, node_data: Dict[str, Any], index: int) -> str:
        """Generate node ID and maintain label mapping."""
        node_id = f"{node_data.get('type', 'node')}_{uuid.uuid4().hex[:8]}"
        label = node_data.get('label', f"Node_{index}")
        
        # Maintain bidirectional mapping
        self.label_to_node_id[label] = node_id
        self.node_id_to_label[node_id] = label
        
        return node_id
    
    def extract_node_properties(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract node properties including label and person assignment."""
        properties = {'label': node_data.get('label', '')}
        
        # Assign person if specified
        if 'person' in node_data and node_data['person'] in self.person_label_to_id:
            properties['personId'] = self.person_label_to_id[node_data['person']]
        
        # Add props
        if 'props' in node_data:
            properties.update(node_data['props'])
        
        return properties
    
    def post_process_diagram(self, diagram: DomainDiagram, data: Dict[str, Any]) -> None:
        """Process persons and metadata after nodes and edges."""
        # Clear mappings for next use
        self.label_to_node_id.clear()
        self.node_id_to_label.clear()
        
        # Convert persons
        self._process_persons(diagram, data)
        
        # Create metadata
        diagram.metadata = DiagramMetadata(
            name=data.get('name', 'Imported Diagram'),
            description=data.get('description', ''),
            version='2.0.0'
        )
        
        # Convert arrows from edges
        diagram.arrows = {}
        for edge in diagram.edges.values():
            arrow = DomainArrow(
                id=edge.id,
                source=edge.source,
                target=edge.target,
                data=edge.data if hasattr(edge, 'data') else {}
            )
            diagram.arrows[arrow.id] = arrow
        
        # Clear edges as light format uses arrows
        diagram.edges = {}
    
    def _process_persons(self, diagram: DomainDiagram, data: Dict[str, Any]) -> None:
        """Process persons from light YAML data."""
        diagram.persons = {}
        diagram.api_keys = {}
        
        for person_data in data.get('persons', []):
            person_id = f"person_{uuid.uuid4().hex[:8]}"
            label = person_data['label']
            self.person_label_to_id[label] = person_id
            self.person_id_to_label[person_id] = label
            
            # Create a default API key for the person
            api_key_id = f"apikey_{uuid.uuid4().hex[:8]}"
            diagram.api_keys[api_key_id] = DomainApiKey(
                id=api_key_id,
                label=f"{label}_key",
                service=LLMService(person_data['service']),
                key="YOUR_API_KEY_HERE"  # Placeholder
            )
            
            diagram.persons[person_id] = DomainPerson(
                id=person_id,
                label=label,
                service=LLMService(person_data['service']),
                model=person_data['model'],
                systemPrompt=person_data.get('systemPrompt'),
                api_key_id=api_key_id,
                forgettingMode=ForgettingMode(person_data.get('forgettingMode', 'none'))
            )
    
    def _calculate_format_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence that this is light YAML format."""
        confidence = 0.0
        
        # Check for version marker
        if data.get('version') == 'light':
            confidence += 0.5
        
        # Check for expected structure
        if 'nodes' in data and isinstance(data['nodes'], list):
            confidence += 0.2
            # Check if nodes use labels
            if data['nodes'] and all('label' in node for node in data['nodes'][:3]):
                confidence += 0.2
        
        # Check for connections instead of edges
        if 'connections' in data and isinstance(data['connections'], list):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    # Serialization methods
    def diagram_to_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        """Convert diagram to light YAML data structure."""
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
                'type': node.type if isinstance(node.type, str) else node.type.value,
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
        arrows = diagram.arrows if diagram.arrows else diagram.edges
        for arrow in arrows.values():
            # Extract node IDs from handle IDs (format: "nodeId:handleName")
            source_node_id = arrow.source.split(':')[0]
            target_node_id = arrow.target.split(':')[0]
            
            source_label = node_labels.get(source_node_id, source_node_id)
            target_label = node_labels.get(target_node_id, target_node_id)
            
            light_arrow = {
                'from': source_label,
                'to': target_label
            }
            
            arrow_data = arrow.data if hasattr(arrow, 'data') else {}
            if arrow_data:
                light_arrow['data'] = arrow_data
            
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
        
        return data