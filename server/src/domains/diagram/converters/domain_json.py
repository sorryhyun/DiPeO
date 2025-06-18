"""Domain JSON format converter."""
import json
from typing import Dict, Any, List
from .base import DiagramConverter
from .shared_components import HandleGenerator, PositionCalculator
from ..models.domain import (
    DomainDiagram, DomainNode, DomainArrow, DomainHandle,
    DomainPerson, DomainApiKey, DiagramMetadata,
    NodeType, HandleDirection, DataType, LLMService, ForgettingMode,
    Vec2
)


class DomainJsonConverter(DiagramConverter):
    """Converts between DomainDiagram and Domain JSON format.
    
    Domain JSON is the canonical format that preserves all diagram structure
    and data in JSON format, compatible with the backend execution engine.
    """
    
    def __init__(self):
        super().__init__()
        self.handle_generator = HandleGenerator()
        self.position_calculator = PositionCalculator()
    
    def serialize(self, diagram: DomainDiagram) -> str:
        """Convert domain diagram to JSON format."""
        # Convert to dict format with objects (not arrays) for easy access by ID
        data = {
            'version': diagram.metadata.version if diagram.metadata else '2.0.0',
            'nodes': {},
            'handles': {},
            'arrows': {},
            'persons': {},
            'api_keys': {}
        }
        
        # Convert nodes - use lowercase enum values for compatibility
        for node_id, node in diagram.nodes.items():
            data['nodes'][node_id] = {
                'id': node.id,
                'type': node.type.value,  # Use lowercase enum value
                'position': {
                    'x': node.position.x,
                    'y': node.position.y
                },
                'data': node.data or {}
            }
        
        # Convert handles - use lowercase enum values for compatibility
        for handle_id, handle in diagram.handles.items():
            data['handles'][handle_id] = {
                'id': handle.id,
                'nodeId': handle.nodeId,
                'label': handle.label,
                'direction': handle.direction.value,  # Use lowercase enum value
                'dataType': handle.dataType.value,  # Use lowercase enum value
                'position': handle.position
            }
        
        # Convert arrows
        for arrow_id, arrow in diagram.arrows.items():
            data['arrows'][arrow_id] = {
                'id': arrow.id,
                'source': arrow.source,
                'target': arrow.target,
                'data': arrow.data or {}
            }
        
        # Convert persons - use lowercase enum values for compatibility
        for person_id, person in diagram.persons.items():
            data['persons'][person_id] = {
                'id': person.id,
                'label': person.label,
                'service': person.service.value,  # Use lowercase enum value
                'model': person.model,
                'apiKeyId': person.api_key_id,
                'systemPrompt': person.systemPrompt,
                'forgettingMode': person.forgettingMode.value,  # Use lowercase enum value
                'type': person.type
            }
        
        # Convert API keys - use lowercase enum values for compatibility
        for key_id, api_key in diagram.api_keys.items():
            data['api_keys'][key_id] = {
                'id': api_key.id,
                'label': api_key.label,
                'service': api_key.service.value,  # Use lowercase enum value
                'key': api_key.key  # In real usage, this should be encrypted
            }
        
        # Add metadata if present
        if diagram.metadata:
            data['metadata'] = {
                'id': diagram.metadata.id,
                'name': diagram.metadata.name,
                'description': diagram.metadata.description,
                'version': diagram.metadata.version,
                'created': diagram.metadata.created.isoformat() if hasattr(diagram.metadata.created, 'isoformat') else str(diagram.metadata.created),
                'modified': diagram.metadata.modified.isoformat() if hasattr(diagram.metadata.modified, 'isoformat') else str(diagram.metadata.modified),
                'author': diagram.metadata.author,
                'tags': diagram.metadata.tags
            }
        
        return json.dumps(data, indent=2, sort_keys=False)
    
    def deserialize(self, content: str) -> DomainDiagram:
        """Convert JSON to domain diagram."""
        data = json.loads(content)
        
        if not isinstance(data, dict):
            raise ValueError("Invalid JSON: expected a dictionary at root level")
        
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
            node_index = 0
            for node_id, node_data in data['nodes'].items():
                # Use position from data, or calculate default position
                pos = node_data.get('position')
                if pos:
                    position = Vec2(x=pos['x'], y=pos['y'])
                else:
                    # Use position calculator for default position
                    position = self.position_calculator.calculate_grid_position(node_index)
                    node_index += 1
                
                diagram.nodes[node_id] = DomainNode(
                    id=node_data.get('id', node_id),
                    type=NodeType(node_data['type']),
                    position=position,
                    data=node_data.get('data', {})
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
        
        # Parse arrows
        if 'arrows' in data:
            for arrow_id, arrow_data in data['arrows'].items():
                diagram.arrows[arrow_id] = DomainArrow(
                    id=arrow_data.get('id', arrow_id),
                    source=arrow_data['source'],
                    target=arrow_data['target'],
                    data=arrow_data.get('data')
                )
        
        # Parse persons
        if 'persons' in data:
            for person_id, person_data in data['persons'].items():
                # Handle forgetting mode with backward compatibility
                forgetting_mode_str = person_data.get('forgettingMode', 'no_forget')
                if forgetting_mode_str == 'no_forget':
                    forgetting_mode = ForgettingMode.NONE
                else:
                    forgetting_mode = ForgettingMode(forgetting_mode_str)
                
                diagram.persons[person_id] = DomainPerson(
                    id=person_data.get('id', person_id),
                    label=person_data['label'],
                    service=LLMService(person_data['service']),
                    model=person_data['model'],
                    api_key_id=person_data.get('apiKeyId'),
                    systemPrompt=person_data.get('systemPrompt'),
                    forgettingMode=forgetting_mode,
                    type=person_data.get('type', 'person')
                )
        
        # Parse API keys
        if 'api_keys' in data:
            for key_id, key_data in data['api_keys'].items():
                diagram.api_keys[key_id] = DomainApiKey(
                    id=key_data.get('id', key_id),
                    label=key_data['label'],
                    service=LLMService(key_data['service']),
                    key=key_data['key']
                )
        
        # Generate default handles for nodes that don't have handles
        for node_id, node in diagram.nodes.items():
            # Check if node has any handles
            node_handles = [h for h in diagram.handles.values() if h.nodeId == node_id]
            if not node_handles:
                # Generate default handles based on node type
                self.handle_generator.generate_for_node(diagram, node_id, node.type.value)
        
        return diagram
    
    def detect_format_confidence(self, content: str) -> float:
        """Detect if content is Domain JSON format."""
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                return 0.0
            
            score = 0.0
            
            # Check for version field (strong indicator)
            if 'version' in data:
                score += 0.2
            
            # Check for required object-based structure (not arrays)
            if 'nodes' in data and isinstance(data['nodes'], dict):
                score += 0.3
            if 'arrows' in data and isinstance(data['arrows'], dict):
                score += 0.2
            if 'handles' in data and isinstance(data['handles'], dict):
                score += 0.1
            
            # Check for domain-specific fields
            if 'persons' in data:
                score += 0.1
            if 'api_keys' in data:
                score += 0.1
            
            return min(score, 1.0)
        except:
            return 0.0