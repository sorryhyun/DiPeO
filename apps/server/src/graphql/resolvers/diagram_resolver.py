"""Diagram resolvers for GraphQL queries and mutations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..types.domain import Diagram, Node, Handle, Arrow, Person, ApiKey, DiagramMetadata
from ..types.scalars import DiagramID
from ..types.inputs import DiagramFilterInput
from ...services.diagram_service import DiagramService
from ...utils.app_context import get_app_context

logger = logging.getLogger(__name__)

class DiagramResolver:
    """Resolver for diagram-related queries and mutations."""
    
    async def get_diagram(self, diagram_id: DiagramID, info) -> Optional[Diagram]:
        """Get a single diagram by ID (loads from file path)."""
        try:
            # Get diagram service from context
            app_context = get_app_context()
            diagram_service: DiagramService = app_context.diagram_service
            
            # The diagram_id is expected to be the file path relative to diagrams directory
            diagram_data = diagram_service.load_diagram(diagram_id)
            
            # Convert domain format to GraphQL Diagram type
            # Extract metadata from the loaded data
            metadata = DiagramMetadata(
                id=diagram_id,
                name=diagram_id.replace('/', ' - ').replace('.yaml', '').replace('.yml', '').replace('.json', '').replace('_', ' ').title(),
                description=diagram_data.get('description', ''),
                created=diagram_data.get('created', datetime.now()),
                modified=diagram_data.get('modified', datetime.now()),
                version=diagram_data.get('version', '1.0')
            )
            
            # Convert nodes from Record to list format
            nodes = []
            for node_id, node_data in diagram_data.get('nodes', {}).items():
                nodes.append(Node(
                    id=node_id,
                    type=node_data.get('type', ''),
                    position=node_data.get('position', {}),
                    data=node_data.get('data', {})
                ))
            
            # Convert arrows from Record to list format
            arrows = []
            for arrow_id, arrow_data in diagram_data.get('arrows', {}).items():
                arrows.append(Arrow(
                    id=arrow_id,
                    source=arrow_data.get('source', ''),
                    target=arrow_data.get('target', ''),
                    data=arrow_data.get('data', {})
                ))
            
            # Convert handles from Record to list format
            handles = []
            for handle_id, handle_data in diagram_data.get('handles', {}).items():
                handles.append(Handle(
                    id=handle_id,
                    nodeId=handle_data.get('nodeId', ''),
                    label=handle_data.get('label', ''),
                    direction=handle_data.get('direction', ''),
                    dataType=handle_data.get('dataType', 'any'),
                    position=handle_data.get('position', '')
                ))
            
            # Convert persons from Record to list format
            persons = []
            for person_id, person_data in diagram_data.get('persons', {}).items():
                persons.append(Person(
                    id=person_id,
                    label=person_data.get('label', ''),
                    service=person_data.get('service', 'openai'),
                    modelName=person_data.get('modelName', 'gpt-4'),
                    systemPrompt=person_data.get('systemPrompt'),
                    apiKeyId=person_data.get('apiKeyId'),
                    contextCleaningRule=person_data.get('contextCleaningRule', 'no_forget')
                ))
            
            # Convert API keys from Record to list format
            api_keys = []
            for key_id, key_data in diagram_data.get('apiKeys', {}).items():
                api_keys.append(ApiKey(
                    id=key_id,
                    label=key_data.get('label', ''),
                    service=key_data.get('service', '')
                ))
            
            # Create and return Diagram object
            diagram = Diagram(
                nodes=nodes,
                arrows=arrows,
                handles=handles,
                persons=persons,
                api_keys=api_keys
            )
            diagram.metadata = metadata
            return diagram
            
        except Exception as e:
            logger.error(f"Failed to get diagram {diagram_id}: {e}")
            return None
    
    async def list_diagrams(
        self, 
        filter: Optional[DiagramFilterInput],
        limit: int,
        offset: int,
        info
    ) -> List[Diagram]:
        """List diagrams with optional filtering."""
        try:
            # Get diagram service from context
            app_context = get_app_context()
            diagram_service: DiagramService = app_context.diagram_service
            
            # Get all diagram files
            all_diagrams = diagram_service.list_diagram_files()
            
            # Apply filtering if provided
            filtered_diagrams = all_diagrams
            if filter:
                # Filter by name
                if filter.name:
                    filtered_diagrams = [
                        d for d in filtered_diagrams 
                        if filter.name.lower() in d['name'].lower()
                    ]
                
                # Filter by format
                if filter.format:
                    filtered_diagrams = [
                        d for d in filtered_diagrams 
                        if d['format'] == filter.format
                    ]
                
                # Filter by modified date
                if filter.modifiedAfter:
                    filtered_diagrams = [
                        d for d in filtered_diagrams 
                        if datetime.fromisoformat(d['modified']) >= filter.modifiedAfter
                    ]
                
                if filter.modifiedBefore:
                    filtered_diagrams = [
                        d for d in filtered_diagrams 
                        if datetime.fromisoformat(d['modified']) <= filter.modifiedBefore
                    ]
            
            # Apply pagination
            start = offset
            end = offset + limit
            paginated_diagrams = filtered_diagrams[start:end]
            
            # Convert to Diagram objects with minimal data (metadata only for listing)
            result = []
            for diagram_info in paginated_diagrams:
                metadata = DiagramMetadata(
                    id=diagram_info['path'],  # Use path as ID for loading
                    name=diagram_info['name'],
                    description=f"Format: {diagram_info['format']}, Size: {diagram_info['size']} bytes",
                    created=datetime.fromisoformat(diagram_info['modified']),  # Use modified as created for now
                    modified=datetime.fromisoformat(diagram_info['modified']),
                    version='1.0'
                )
                
                # Create a minimal Diagram object with just metadata
                diagram = Diagram(
                    nodes=[],
                    arrows=[],
                    handles=[],
                    persons=[],
                    api_keys=[]
                )
                diagram.metadata = metadata
                result.append(diagram)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list diagrams: {e}")
            return []

diagram_resolver = DiagramResolver()