"""Enhanced Domain JSON format converter using the new base classes."""
from typing import Dict, Any, List, Optional
from .base import JsonBasedConverter
from ..models.domain import (
    DomainDiagram, DomainNode, DomainArrow, DomainHandle,
    DomainPerson, DomainApiKey, DiagramMetadata,
    NodeType, HandleDirection, DataType, LLMService, ForgettingMode,
    Vec2
)


class EnhancedDomainJsonConverter(JsonBasedConverter):
    """Enhanced Domain JSON converter that uses shared components.
    
    Domain JSON is the canonical format that preserves all diagram structure
    and data in JSON format, compatible with the backend execution engine.
    """
    
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract node data from parsed content."""
        nodes = data.get('nodes', {})
        # Convert dict of nodes to list for processing
        return list(nodes.values()) if isinstance(nodes, dict) else nodes
    
    def extract_arrows(self, data: Dict[str, Any], diagram: DomainDiagram) -> List[Dict[str, Any]]:
        """Extract arrow data from parsed content."""
        arrows = data.get('arrows', {})
        # Convert dict of arrows to list for processing
        arrow_list = list(arrows.values()) if isinstance(arrows, dict) else arrows
        
        # For domain JSON, arrows already have all required fields
        return arrow_list
    
    def should_generate_handles(self, node_data: Dict[str, Any]) -> bool:
        """Domain JSON should not generate handles - they should be explicit."""
        return False
    
    def post_process_diagram(self, diagram: DomainDiagram, original_data: Dict[str, Any]) -> None:
        """Post-process to add handles, persons, and API keys."""
        # Add handles from data
        handles = original_data.get('handles', {})
        for handle_id, handle_data in handles.items():
            if isinstance(handle_data, dict):
                handle = DomainHandle(
                    id=handle_data.get('id', handle_id),
                    nodeId=handle_data.get('nodeId', ''),
                    direction=HandleDirection(handle_data.get('direction', 'inout'))
                )
                diagram.handles[handle.id] = handle
        
        # Add persons from data
        persons = original_data.get('persons', {})
        for person_id, person_data in persons.items():
            if isinstance(person_data, dict):
                person = DomainPerson(
                    id=person_data.get('id', person_id),
                    name=person_data.get('name', ''),
                    api_key=person_data.get('api_key'),
                    forgetting_mode=ForgettingMode(person_data.get('forgetting_mode', 'keep'))
                )
                diagram.persons[person.id] = person
        
        # Add API keys from data
        api_keys = original_data.get('api_keys', {})
        for key_id, key_data in api_keys.items():
            if isinstance(key_data, dict):
                api_key = DomainApiKey(
                    id=key_data.get('id', key_id),
                    name=key_data.get('name', ''),
                    service=LLMService(key_data.get('service', 'openai')),
                    api_key=key_data.get('api_key', ''),
                    models=key_data.get('models', [])
                )
                diagram.api_keys[api_key.id] = api_key
        
        # Add metadata
        metadata_data = original_data.get('metadata', {})
        if metadata_data:
            diagram.metadata = DiagramMetadata(
                version=metadata_data.get('version', '2.0.0'),
                created_at=metadata_data.get('created_at'),
                updated_at=metadata_data.get('updated_at'),
                title=metadata_data.get('title'),
                description=metadata_data.get('description')
            )
    
    def extract_node_type(self, node_data: Dict[str, Any]) -> str:
        """Extract node type - Domain JSON uses lowercase enum values."""
        node_type = node_data.get('type', 'unknown')
        # Ensure it's a valid NodeType
        try:
            NodeType(node_type)
            return node_type
        except ValueError:
            # Use mapper for fallback
            return super().extract_node_type(node_data)
    
    def extract_node_position(self, node_data: Dict[str, Any], index: int) -> Dict[str, float]:
        """Extract node position - Domain JSON always has positions."""
        pos = node_data.get('position', {})
        if isinstance(pos, dict) and 'x' in pos and 'y' in pos:
            return pos
        # Fallback to default positioning
        return super().extract_node_position(node_data, index)
    
    def extract_node_properties(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract node properties - Domain JSON uses 'data' field."""
        return node_data.get('data', {})
    
    def diagram_to_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        """Convert diagram to Domain JSON format."""
        data = {
            'version': diagram.metadata.version if diagram.metadata else '2.0.0',
            'nodes': {},
            'handles': {},
            'arrows': {},
            'persons': {},
            'api_keys': {}
        }
        
        # Convert nodes
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
        
        # Convert handles
        for handle_id, handle in diagram.handles.items():
            data['handles'][handle_id] = {
                'id': handle.id,
                'nodeId': handle.nodeId,
                'direction': handle.direction.value
            }
        
        # Convert arrows
        for arrow_id, arrow in diagram.arrows.items():
            data['arrows'][arrow_id] = {
                'id': arrow.id,
                'source': arrow.source,
                'target': arrow.target
            }
        
        # Convert persons
        for person_id, person in diagram.persons.items():
            person_data = {
                'id': person.id,
                'name': person.name,
                'forgetting_mode': person.forgetting_mode.value
            }
            if person.api_key:
                person_data['api_key'] = person.api_key
            data['persons'][person_id] = person_data
        
        # Convert API keys
        for key_id, api_key in diagram.api_keys.items():
            data['api_keys'][key_id] = {
                'id': api_key.id,
                'name': api_key.name,
                'service': api_key.service.value,
                'api_key': api_key.api_key,
                'models': api_key.models or []
            }
        
        # Add metadata if present
        if diagram.metadata:
            data['metadata'] = {
                'version': diagram.metadata.version,
                'created_at': diagram.metadata.created_at,
                'updated_at': diagram.metadata.updated_at,
                'title': diagram.metadata.title,
                'description': diagram.metadata.description
            }
        
        return data
    
    def _calculate_format_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score for Domain JSON format."""
        confidence = 0.0
        
        # Check for version field (strong indicator)
        if 'version' in data:
            confidence += 0.3
        
        # Check for expected structure
        expected_keys = {'nodes', 'handles', 'arrows'}
        if expected_keys.issubset(data.keys()):
            confidence += 0.4
        
        # Check if nodes have the expected structure
        nodes = data.get('nodes', {})
        if nodes and isinstance(nodes, dict):
            sample_node = next(iter(nodes.values()), {})
            if all(key in sample_node for key in ['id', 'type', 'position']):
                confidence += 0.3
        
        return min(confidence, 1.0)