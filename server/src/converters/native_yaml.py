"""Native YAML format converter - full fidelity."""
import yaml
from typing import Dict, Any, List
from .base import DiagramConverter
from ..domain import (
    DomainDiagram, DomainNode, DomainArrow, DomainHandle, 
    DomainPerson, DomainApiKey, DiagramMetadata, Vec2,
    NodeType, HandleDirection, DataType, LLMService, ForgettingMode
)


class NativeYamlConverter(DiagramConverter):
    """Converts between DomainDiagram and native YAML format."""
    
    def serialize(self, diagram: DomainDiagram) -> str:
        """Convert domain diagram to native YAML."""
        # Convert to dict format for YAML serialization
        data = {
            'version': diagram.metadata.version if diagram.metadata else '2.0.0',
            'nodes': {},
            'arrows': {},
            'handles': {},
            'persons': {},
            'apiKeys': {}
        }
        
        # Convert nodes
        for node_id, node in diagram.nodes.items():
            data['nodes'][node_id] = {
                'id': node.id,
                'type': node.type.value,
                'position': {'x': node.position.x, 'y': node.position.y},
                'data': node.data
            }
        
        # Convert arrows
        for arrow_id, arrow in diagram.arrows.items():
            data['arrows'][arrow_id] = {
                'id': arrow.id,
                'source': arrow.source,
                'target': arrow.target,
                'data': arrow.data or {}
            }
        
        # Convert handles
        for handle_id, handle in diagram.handles.items():
            data['handles'][handle_id] = {
                'id': handle.id,
                'nodeId': handle.nodeId,
                'label': handle.label,
                'direction': handle.direction.value,
                'dataType': handle.dataType.value,
                'position': handle.position
            }
        
        # Convert persons
        for person_id, person in diagram.persons.items():
            data['persons'][person_id] = {
                'id': person.id,
                'label': person.label,
                'service': person.service.value,
                'model': person.model,
                'apiKeyId': person.apiKeyId,
                'systemPrompt': person.systemPrompt,
                'forgettingMode': person.forgettingMode.value,
                'type': person.type
            }
        
        # Convert API keys
        for key_id, api_key in diagram.api_keys.items():
            data['apiKeys'][key_id] = {
                'id': api_key.id,
                'label': api_key.label,
                'service': api_key.service.value,
                'key': api_key.key  # In real usage, this should be encrypted
            }
        
        # Add metadata if present
        if diagram.metadata:
            data['metadata'] = {
                'id': diagram.metadata.id,
                'name': diagram.metadata.name,
                'description': diagram.metadata.description,
                'version': diagram.metadata.version,
                'created': diagram.metadata.created.isoformat(),
                'modified': diagram.metadata.modified.isoformat(),
                'author': diagram.metadata.author,
                'tags': diagram.metadata.tags
            }
        
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def deserialize(self, content: str) -> DomainDiagram:
        """Convert native YAML to domain diagram."""
        data = yaml.safe_load(content)
        
        if not isinstance(data, dict):
            raise ValueError("Invalid YAML: expected a dictionary at root level")
        
        # Initialize empty diagram
        diagram = DomainDiagram(
            nodes={},
            arrows={},
            handles={},
            persons={},
            api_keys={},
            metadata=None
        )
        
        # Parse metadata
        if 'metadata' in data:
            meta = data['metadata']
            diagram.metadata = DiagramMetadata(
                id=meta.get('id'),
                name=meta.get('name'),
                description=meta.get('description'),
                version=meta.get('version', '2.0.0'),
                author=meta.get('author'),
                tags=meta.get('tags')
            )
        
        # Parse nodes
        if 'nodes' in data:
            for node_id, node_data in data['nodes'].items():
                pos = node_data.get('position', {'x': 0, 'y': 0})
                diagram.nodes[node_id] = DomainNode(
                    id=node_data.get('id', node_id),
                    type=NodeType(node_data['type']),
                    position=Vec2(x=pos['x'], y=pos['y']),
                    data=node_data.get('data', {})
                )
        
        # Parse arrows
        if 'arrows' in data:
            for arrow_id, arrow_data in data['arrows'].items():
                diagram.arrows[arrow_id] = DomainArrow(
                    id=arrow_data.get('id', arrow_id),
                    source=arrow_data['source'],
                    target=arrow_data['target'],
                    data=arrow_data.get('data')
                )
        
        # Parse handles
        if 'handles' in data:
            for handle_id, handle_data in data['handles'].items():
                diagram.handles[handle_id] = DomainHandle(
                    id=handle_data.get('id', handle_id),
                    nodeId=handle_data['nodeId'],
                    label=handle_data['label'],
                    direction=HandleDirection(handle_data['direction']),
                    dataType=DataType(handle_data.get('dataType', 'any')),
                    position=handle_data.get('position')
                )
        
        # Parse persons
        if 'persons' in data:
            for person_id, person_data in data['persons'].items():
                diagram.persons[person_id] = DomainPerson(
                    id=person_data.get('id', person_id),
                    label=person_data['label'],
                    service=LLMService(person_data['service']),
                    model=person_data['model'],
                    apiKeyId=person_data['apiKeyId'],
                    systemPrompt=person_data.get('systemPrompt'),
                    forgettingMode=ForgettingMode(person_data.get('forgettingMode', 'none')),
                    type=person_data.get('type', 'person')
                )
        
        # Parse API keys
        if 'apiKeys' in data:
            for key_id, key_data in data['apiKeys'].items():
                diagram.api_keys[key_id] = DomainApiKey(
                    id=key_data.get('id', key_id),
                    label=key_data['label'],
                    service=LLMService(key_data['service']),
                    key=key_data['key']
                )
        
        return diagram
    
    def detect_format_confidence(self, content: str) -> float:
        """Detect if content is native YAML format."""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return 0.0
            
            # Check for native format indicators
            score = 0.0
            if 'version' in data:
                score += 0.2
            if 'nodes' in data and isinstance(data['nodes'], dict):
                score += 0.3
            if 'arrows' in data and isinstance(data['arrows'], dict):
                score += 0.2
            if 'handles' in data:
                score += 0.15
            if 'persons' in data:
                score += 0.15
            
            return min(score, 1.0)
        except:
            return 0.0