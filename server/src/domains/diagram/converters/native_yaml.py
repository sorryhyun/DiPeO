"""Native YAML format converter."""
import yaml
from typing import Dict, Any, List
from .base import DiagramConverter
from ..models.domain import (
    DomainDiagram, DomainNode, DomainArrow, DomainHandle,
    DomainPerson, DomainApiKey, DiagramMetadata,
    NodeType, HandleDirection, DataType, LLMService, ForgettingMode,
    Vec2
)


class NativeYamlConverter(DiagramConverter):
    """Converts between DomainDiagram and Native YAML format.
    
    Native YAML preserves all GraphQL schema fields in YAML format.
    It preserves all fields exactly as they are in the GraphQL schema.
    """
    
    def serialize(self, diagram: DomainDiagram) -> str:
        """Convert domain diagram to native YAML format."""
        # Convert to dict format matching GraphQL schema
        data = {
            'nodes': [self._serialize_node(node) for node in diagram.nodes.values()],
            'handles': [self._serialize_handle(handle) for handle in diagram.handles.values()],
            'arrows': [self._serialize_arrow(arrow) for arrow in diagram.arrows.values()],
            'persons': [self._serialize_person(person) for person in diagram.persons.values()],
            'apiKeys': [self._serialize_api_key(key) for key in diagram.apiKeys.values()],
        }
        
        # Add metadata if present
        if diagram.metadata:
            data['metadata'] = self._serialize_metadata(diagram.metadata)
        
        return yaml.dump(data, default_flow_style=False, sort_keys=False, 
                        allow_unicode=True, width=120)
    
    def deserialize(self, content: str) -> DomainDiagram:
        """Convert native YAML to domain diagram."""
        data = yaml.safe_load(content)
        
        # Parse nodes
        nodes = {}
        for node_data in data.get('nodes', []):
            node = self._deserialize_node(node_data)
            nodes[node.id] = node
        
        # Parse handles
        handles = {}
        for handle_data in data.get('handles', []):
            handle = self._deserialize_handle(handle_data)
            handles[handle.id] = handle
        
        # Parse arrows
        arrows = {}
        for arrow_data in data.get('arrows', []):
            arrow = self._deserialize_arrow(arrow_data)
            arrows[arrow.id] = arrow
        
        # Parse persons
        persons = {}
        for person_data in data.get('persons', []):
            person = self._deserialize_person(person_data)
            persons[person.id] = person
        
        # Parse API keys
        api_keys = {}
        for key_data in data.get('apiKeys', []):
            api_key = self._deserialize_api_key(key_data)
            api_keys[api_key.id] = api_key
        
        # Parse metadata
        metadata = None
        if 'metadata' in data:
            metadata = self._deserialize_metadata(data['metadata'])
        
        return DomainDiagram(
            nodes=nodes,
            handles=handles,
            arrows=arrows,
            persons=persons,
            apiKeys=api_keys,
            metadata=metadata
        )
    
    def _serialize_node(self, node: DomainNode) -> Dict[str, Any]:
        """Serialize a node to dict."""
        return {
            'id': node.id,
            'type': node.type.value,
            'position': {
                'x': node.position.x,
                'y': node.position.y
            },
            'data': node.data,
            'displayName': node.displayName
        }
    
    def _serialize_handle(self, handle: DomainHandle) -> Dict[str, Any]:
        """Serialize a handle to dict."""
        return {
            'id': handle.id,
            'nodeId': handle.nodeId,
            'label': handle.label,
            'direction': handle.direction.value,
            'dataType': handle.dataType.value,
            'position': handle.position
        }
    
    def _serialize_arrow(self, arrow: DomainArrow) -> Dict[str, Any]:
        """Serialize an arrow to dict."""
        return {
            'id': arrow.id,
            'source': arrow.source,
            'target': arrow.target,
            'data': arrow.data
        }
    
    def _serialize_person(self, person: DomainPerson) -> Dict[str, Any]:
        """Serialize a person to dict."""
        return {
            'id': person.id,
            'label': person.label,
            'service': person.service.value,
            'model': person.model,
            'apiKeyId': person.apiKeyId,
            'systemPrompt': person.systemPrompt,
            'forgettingMode': person.forgettingMode.value,
            'type': 'person'
        }
    
    def _serialize_api_key(self, api_key: DomainApiKey) -> Dict[str, Any]:
        """Serialize an API key to dict."""
        # Never include the actual key in serialization
        return {
            'id': api_key.id,
            'label': api_key.label,
            'service': api_key.service.value,
            'maskedKey': api_key.maskedKey
        }
    
    def _serialize_metadata(self, metadata: DiagramMetadata) -> Dict[str, Any]:
        """Serialize metadata to dict."""
        return {
            'id': metadata.id,
            'name': metadata.name,
            'description': metadata.description,
            'version': metadata.version,
            'created': metadata.created,
            'modified': metadata.modified,
            'author': metadata.author,
            'tags': metadata.tags
        }
    
    def _deserialize_node(self, data: Dict[str, Any]) -> DomainNode:
        """Deserialize a node from dict."""
        return DomainNode(
            id=data['id'],
            type=NodeType(data['type']),
            position=Vec2(x=data['position']['x'], y=data['position']['y']),
            data=data.get('data', {}),
            displayName=data.get('displayName')
        )
    
    def _deserialize_handle(self, data: Dict[str, Any]) -> DomainHandle:
        """Deserialize a handle from dict."""
        return DomainHandle(
            id=data['id'],
            nodeId=data['nodeId'],
            label=data['label'],
            direction=HandleDirection(data['direction']),
            dataType=DataType(data['dataType']),
            position=data.get('position')
        )
    
    def _deserialize_arrow(self, data: Dict[str, Any]) -> DomainArrow:
        """Deserialize an arrow from dict."""
        return DomainArrow(
            id=data['id'],
            source=data['source'],
            target=data['target'],
            data=data.get('data')
        )
    
    def _deserialize_person(self, data: Dict[str, Any]) -> DomainPerson:
        """Deserialize a person from dict."""
        return DomainPerson(
            id=data['id'],
            label=data['label'],
            service=LLMService(data['service']),
            model=data['model'],
            apiKeyId=data.get('apiKeyId'),
            systemPrompt=data.get('systemPrompt'),
            forgettingMode=ForgettingMode(data['forgettingMode']),
            type='person'
        )
    
    def _deserialize_api_key(self, data: Dict[str, Any]) -> DomainApiKey:
        """Deserialize an API key from dict."""
        return DomainApiKey(
            id=data['id'],
            label=data['label'],
            service=LLMService(data['service']),
            maskedKey=data['maskedKey']
        )
    
    def _deserialize_metadata(self, data: Dict[str, Any]) -> DiagramMetadata:
        """Deserialize metadata from dict."""
        return DiagramMetadata(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            version=data['version'],
            created=data['created'],
            modified=data['modified'],
            author=data.get('author'),
            tags=data.get('tags')
        )
    
    def detect_format_confidence(self, content: str) -> float:
        """Detect if content is native YAML format."""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return 0.0
            
            score = 0.0
            
            # Check for required fields
            if 'nodes' in data and isinstance(data['nodes'], list):
                score += 0.2
            if 'handles' in data and isinstance(data['handles'], list):
                score += 0.2
            if 'arrows' in data and isinstance(data['arrows'], list):
                score += 0.2
                
            # Check for native format indicators
            if data.get('nodes'):
                node = data['nodes'][0]
                if all(key in node for key in ['id', 'type', 'position']):
                    score += 0.2
                if 'position' in node and isinstance(node['position'], dict):
                    if 'x' in node['position'] and 'y' in node['position']:
                        score += 0.1
                        
            # Check for handles (native format has separate handles)
            if data.get('handles'):
                handle = data['handles'][0]
                if all(key in handle for key in ['id', 'nodeId', 'direction']):
                    score += 0.1
            
            return min(score, 1.0)
        except:
            return 0.0