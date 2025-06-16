"""Native JSON format converter - uses GraphQL schema format directly."""
import json
from typing import Dict, Any, List
from .base import DiagramConverter
from ..domain import (
    DomainDiagram, DomainNode, DomainArrow, DomainHandle, 
    DomainPerson, DomainApiKey, DiagramMetadata, Vec2,
    NodeType, HandleDirection, DataType, LLMService, ForgettingMode
)


class NativeJsonConverter(DiagramConverter):
    """Converts between DomainDiagram and native JSON format using GraphQL schema format."""
    
    # GraphQL enum mappings
    NODE_TYPE_TO_GRAPHQL = {
        NodeType.START: "START",
        NodeType.PERSON_JOB: "PERSON_JOB",
        NodeType.PERSON_BATCH_JOB: "PERSON_BATCH_JOB",
        NodeType.CONDITION: "CONDITION",
        NodeType.JOB: "JOB",
        NodeType.ENDPOINT: "ENDPOINT",
        NodeType.DB: "DB",
        NodeType.USER_RESPONSE: "USER_RESPONSE",
        NodeType.NOTION: "NOTION"
    }
    
    GRAPHQL_TO_NODE_TYPE = {v: k for k, v in NODE_TYPE_TO_GRAPHQL.items()}
    
    HANDLE_DIRECTION_TO_GRAPHQL = {
        HandleDirection.INPUT: "INPUT",
        HandleDirection.OUTPUT: "OUTPUT"
    }
    
    GRAPHQL_TO_HANDLE_DIRECTION = {v: k for k, v in HANDLE_DIRECTION_TO_GRAPHQL.items()}
    
    DATA_TYPE_TO_GRAPHQL = {
        DataType.ANY: "ANY",
        DataType.STRING: "STRING",
        DataType.NUMBER: "NUMBER",
        DataType.BOOLEAN: "BOOLEAN",
        DataType.OBJECT: "OBJECT",
        DataType.ARRAY: "ARRAY"
    }
    
    GRAPHQL_TO_DATA_TYPE = {v: k for k, v in DATA_TYPE_TO_GRAPHQL.items()}
    
    LLM_SERVICE_TO_GRAPHQL = {
        LLMService.OPENAI: "OPENAI",
        LLMService.ANTHROPIC: "ANTHROPIC",
        LLMService.GOOGLE: "GOOGLE",
        LLMService.GROK: "GROK",
        LLMService.BEDROCK: "BEDROCK",
        LLMService.VERTEX: "VERTEX",
        LLMService.DEEPSEEK: "DEEPSEEK"
    }
    
    GRAPHQL_TO_LLM_SERVICE = {v: k for k, v in LLM_SERVICE_TO_GRAPHQL.items()}
    
    FORGETTING_MODE_TO_GRAPHQL = {
        ForgettingMode.NO_FORGET: "NO_FORGET",
        ForgettingMode.NONE: "NONE",
        ForgettingMode.ON_EVERY_TURN: "ON_EVERY_TURN",
        ForgettingMode.UPON_REQUEST: "UPON_REQUEST"
    }
    
    GRAPHQL_TO_FORGETTING_MODE = {v: k for k, v in FORGETTING_MODE_TO_GRAPHQL.items()}
    
    def serialize(self, diagram: DomainDiagram) -> str:
        """Convert domain diagram to native JSON using GraphQL format."""
        # Convert to dict format for JSON serialization
        data = {
            'version': diagram.metadata.version if diagram.metadata else '2.0.0',
            'nodes': {},
            'arrows': {},
            'handles': {},
            'persons': {},
            'api_keys': {}
        }
        
        # Convert nodes - preserve lowercase format for frontend compatibility
        for node_id, node in diagram.nodes.items():
            data['nodes'][node_id] = {
                'id': node.id,
                'type': node.type.value,  # Use lowercase enum value directly
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
        
        # Convert handles - preserve lowercase format for frontend compatibility
        for handle_id, handle in diagram.handles.items():
            data['handles'][handle_id] = {
                'id': handle.id,
                'nodeId': handle.nodeId,
                'label': handle.label,
                'direction': handle.direction.value,  # Use lowercase enum value directly
                'dataType': handle.dataType.value,  # Use lowercase enum value directly
                'position': handle.position
            }
        
        # Convert persons - preserve lowercase format for frontend compatibility
        for person_id, person in diagram.persons.items():
            data['persons'][person_id] = {
                'id': person.id,
                'label': person.label,
                'service': person.service.value,  # Use lowercase enum value directly
                'model': person.model,
                'apiKeyId': person.api_key_id,
                'systemPrompt': person.systemPrompt,
                'forgettingMode': person.forgettingMode.value,  # Use lowercase enum value directly
                'type': person.type
            }
        
        # Convert API keys - preserve lowercase format for frontend compatibility
        for key_id, api_key in diagram.api_keys.items():
            data['api_keys'][key_id] = {
                'id': api_key.id,
                'label': api_key.label,
                'service': api_key.service.value,  # Use lowercase enum value directly
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
        """Convert native JSON to domain diagram."""
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
        
        # Parse nodes - convert from GraphQL format
        if 'nodes' in data:
            for node_id, node_data in data['nodes'].items():
                pos = node_data.get('position', {'x': 0, 'y': 0})
                node_type_str = node_data['type']
                
                # Convert from GraphQL enum to domain enum
                node_type = self.GRAPHQL_TO_NODE_TYPE.get(node_type_str)
                if not node_type:
                    # Fallback: try lowercase conversion
                    node_type = NodeType(node_type_str.lower())
                
                diagram.nodes[node_id] = DomainNode(
                    id=node_data.get('id', node_id),
                    type=node_type,
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
        
        # Parse handles - convert from GraphQL format
        if 'handles' in data:
            for handle_id, handle_data in data['handles'].items():
                direction_str = handle_data['direction']
                direction = self.GRAPHQL_TO_HANDLE_DIRECTION.get(direction_str)
                if not direction:
                    # Fallback: try lowercase conversion
                    direction = HandleDirection(direction_str.lower())
                
                data_type_str = handle_data.get('dataType', 'ANY')
                data_type = self.GRAPHQL_TO_DATA_TYPE.get(data_type_str)
                if not data_type:
                    # Fallback: try lowercase conversion
                    data_type = DataType(data_type_str.lower())
                
                diagram.handles[handle_id] = DomainHandle(
                    id=handle_data.get('id', handle_id),
                    nodeId=handle_data['nodeId'],
                    label=handle_data['label'],
                    direction=direction,
                    dataType=data_type,
                    position=handle_data.get('position')
                )
        
        # Parse persons - convert from GraphQL format
        if 'persons' in data:
            for person_id, person_data in data['persons'].items():
                service_str = person_data['service']
                service = self.GRAPHQL_TO_LLM_SERVICE.get(service_str)
                if not service:
                    # Fallback: try lowercase conversion
                    service = LLMService(service_str.lower())
                
                forgetting_mode_str = person_data.get('forgettingMode', 'NO_FORGET')
                forgetting_mode = self.GRAPHQL_TO_FORGETTING_MODE.get(forgetting_mode_str)
                if not forgetting_mode:
                    # Fallback: handle legacy values
                    if forgetting_mode_str == 'no_forget':
                        forgetting_mode = ForgettingMode.NONE
                    else:
                        forgetting_mode = ForgettingMode(forgetting_mode_str.lower())
                
                diagram.persons[person_id] = DomainPerson(
                    id=person_data.get('id', person_id),
                    label=person_data['label'],
                    service=service,
                    model=person_data['model'],
                    api_key_id=person_data['apiKeyId'],
                    systemPrompt=person_data.get('systemPrompt'),
                    forgettingMode=forgetting_mode,
                    type=person_data.get('type', 'person')
                )
        
        # Parse API keys - convert from GraphQL format
        if 'apiKeys' in data:
            for key_id, key_data in data['apiKeys'].items():
                service_str = key_data['service']
                service = self.GRAPHQL_TO_LLM_SERVICE.get(service_str)
                if not service:
                    # Fallback: try lowercase conversion
                    service = LLMService(service_str.lower())
                
                diagram.api_keys[key_id] = DomainApiKey(
                    id=key_data.get('id', key_id),
                    label=key_data['label'],
                    service=service,
                    key=key_data['key']
                )
        
        return diagram
    
    def detect_format_confidence(self, content: str) -> float:
        """Detect if content is native JSON format."""
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                return 0.0
            
            # Check for native format indicators
            score = 0.0
            if 'version' in data:
                score += 0.2
            if 'nodes' in data and isinstance(data['nodes'], dict):
                score += 0.3
                # Check for GraphQL-style node types
                for node in data['nodes'].values():
                    if 'type' in node and node['type'] in self.GRAPHQL_TO_NODE_TYPE:
                        score += 0.1
                        break
            if 'arrows' in data and isinstance(data['arrows'], dict):
                score += 0.2
            if 'handles' in data:
                score += 0.1
            if 'persons' in data:
                score += 0.1
            
            return min(score, 1.0)
        except:
            return 0.0