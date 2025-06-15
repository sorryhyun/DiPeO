"""
Utilities for converting between internal domain models and GraphQL models.
"""
from typing import Dict, Any
import logging

from ..domain import (
    DomainNode, DomainHandle, DomainArrow,
    DomainPerson, DomainApiKey, DiagramMetadata,
    NodeType, HandleDirection, DataType, LLMService, ForgettingMode,
    Vec2, DiagramForGraphQL
)

logger = logging.getLogger(__name__)

class DomainToGraphQLConverter:
    """Convert internal domain models to GraphQL-ready models."""
    
    @staticmethod
    def convert_diagram(diagram_data: Dict[str, Any]) -> DiagramForGraphQL:
        """Convert a diagram from internal format to GraphQL format."""
        try:
            # Convert nodes
            nodes = []
            for node_id, node_data in diagram_data.get('nodes', {}).items():
                position_data = node_data.get('position', {})
                position = Vec2(x=position_data.get('x', 0), y=position_data.get('y', 0))
                
                node = DomainNode(
                    id=node_id,
                    type=NodeType(node_data.get('type', 'start')),
                    position=position,
                    data=node_data.get('data', {})
                )
                nodes.append(node)
            
            # Convert handles
            handles = []
            for handle_id, handle_data in diagram_data.get('handles', {}).items():
                # Map legacy direction values
                direction_str = handle_data.get('direction', 'input')
                if direction_str in ['in', 'input']:
                    direction = HandleDirection.INPUT
                elif direction_str in ['out', 'output']:
                    direction = HandleDirection.OUTPUT
                else:
                    direction = HandleDirection.INPUT
                
                handle = DomainHandle(
                    id=handle_id,
                    nodeId=handle_data.get('nodeId', ''),
                    label=handle_data.get('label', ''),
                    direction=direction,
                    dataType=DataType(handle_data.get('dataType', 'any')),
                    position=handle_data.get('position')
                )
                handles.append(handle)
            
            # Convert arrows
            arrows = []
            for arrow_id, arrow_data in diagram_data.get('arrows', {}).items():
                arrow = DomainArrow(
                    id=arrow_id,
                    source=arrow_data.get('source', ''),
                    target=arrow_data.get('target', ''),
                    data=arrow_data.get('data')
                )
                arrows.append(arrow)
            
            # Convert persons
            persons = []
            for person_id, person_data in diagram_data.get('persons', {}).items():
                # Map legacy service values
                service_str = person_data.get('service', 'openai')
                if service_str == 'claude':
                    service = LLMService.ANTHROPIC
                elif service_str == 'gemini':
                    service = LLMService.GOOGLE
                elif service_str == 'grok':
                    service = LLMService.GROQ
                else:
                    try:
                        service = LLMService(service_str)
                    except ValueError:
                        service = LLMService.OPENAI
                
                # Map legacy forgetting mode
                forgetting_str = person_data.get('forgettingMode', 'no_forget')
                if forgetting_str == 'no_forget':
                    forgetting_mode = ForgettingMode.NONE
                else:
                    try:
                        forgetting_mode = ForgettingMode(forgetting_str)
                    except ValueError:
                        forgetting_mode = ForgettingMode.NONE
                
                person = DomainPerson(
                    id=person_id,
                    label=person_data.get('label', ''),
                    service=service,
                    model=person_data.get('model', person_data.get('modelName', 'gpt-4')),
                    apiKeyId=person_data.get('apiKeyId', ''),
                    systemPrompt=person_data.get('systemPrompt'),
                    forgettingMode=forgetting_mode,
                    type=person_data.get('type', 'person')
                )
                persons.append(person)
            
            # Convert API keys
            api_keys = []
            for key_id, key_data in diagram_data.get('apiKeys', {}).items():
                # Map service for API keys too
                service_str = key_data.get('service', 'openai')
                if service_str == 'claude':
                    service = LLMService.ANTHROPIC
                elif service_str == 'gemini':
                    service = LLMService.GOOGLE
                elif service_str == 'grok':
                    service = LLMService.GROQ
                else:
                    try:
                        service = LLMService(service_str)
                    except ValueError:
                        service = LLMService.OPENAI
                
                api_key = DomainApiKey(
                    id=key_id,
                    label=key_data.get('label', ''),
                    service=service,
                    key=key_data.get('key', '')  # Will be excluded in GraphQL
                )
                api_keys.append(api_key)
            
            # Convert metadata
            metadata = None
            if 'metadata' in diagram_data and diagram_data['metadata']:
                meta_data = diagram_data['metadata']
                metadata = DiagramMetadata(
                    id=meta_data.get('id'),
                    name=meta_data.get('name'),
                    description=meta_data.get('description'),
                    version=meta_data.get('version', '2.0.0'),
                    created=meta_data.get('created'),
                    modified=meta_data.get('modified'),
                    author=meta_data.get('author'),
                    tags=meta_data.get('tags')
                )
            
            return DiagramForGraphQL(
                nodes=nodes,
                handles=handles,
                arrows=arrows,
                persons=persons,
                api_keys=api_keys,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error converting diagram to GraphQL format: {e}")
            raise
    
    @staticmethod
    def convert_to_internal(graphql_diagram: DiagramForGraphQL) -> Dict[str, Any]:
        """Convert GraphQL diagram back to internal format."""
        return {
            'nodes': {node.id: node.dict() for node in graphql_diagram.nodes},
            'handles': {handle.id: handle.dict() for handle in graphql_diagram.handles},
            'arrows': {arrow.id: arrow.dict() for arrow in graphql_diagram.arrows},
            'persons': {person.id: person.dict() for person in graphql_diagram.persons},
            'apiKeys': {api_key.id: api_key.dict() for api_key in graphql_diagram.api_keys},
            'metadata': graphql_diagram.metadata.dict() if graphql_diagram.metadata else None
        }