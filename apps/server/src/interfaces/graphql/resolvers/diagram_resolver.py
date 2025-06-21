"""Refactored diagram resolvers using Pydantic models as single source of truth."""
from typing import Optional, List
from datetime import datetime
from collections import defaultdict
import logging

from ..types.domain import DomainDiagramType as GraphQLDiagram, DiagramMetadata
from ..types.scalars import DiagramID
from ..types.inputs import DiagramFilterInput
from src.domains.diagram import DiagramService
from src.domains.diagram.converters import diagram_dict_to_graphql
from src.__generated__.models import DiagramDictFormat

logger = logging.getLogger(__name__)

class DiagramResolver:
    """Resolver for diagram-related queries and mutations."""
    
    async def get_diagram(self, diagram_id: DiagramID, info) -> Optional[GraphQLDiagram]:
        """Get a single diagram by ID (loads from file path)."""
        try:
            logger.info(f"Attempting to get diagram with ID: {diagram_id}")
            # Get diagram service from GraphQL context
            diagram_service: DiagramService = info.context.diagram_service
            
            # Load diagram data using get_diagram which handles ID to path conversion
            diagram_data = await diagram_service.get_diagram(diagram_id)
            
            # Check if diagram was found
            if not diagram_data:
                logger.error(f"Diagram not found: {diagram_id}")
                return None
            
            # If metadata is missing, create it
            if 'metadata' not in diagram_data or not diagram_data['metadata']:
                diagram_data['metadata'] = {
                    'id': diagram_id,
                    'name': diagram_id.replace('/', ' - ').replace('.yaml', '').replace('.yml', '').replace('.json', '').replace('_', ' ').title(),
                    'description': diagram_data.get('description', ''),
                    'version': diagram_data.get('version', '2.0.0'),
                    'created': diagram_data.get('created', datetime.now().isoformat()),
                    'modified': diagram_data.get('modified', datetime.now().isoformat())
                }
            
            # Convert to DomainDiagram then to GraphQL format
            diagram_dict = DiagramDictFormat.model_validate(diagram_data)
            graphql_diagram = diagram_dict_to_graphql(diagram_dict)
            
            # Build handle_index for nested view
            handle_index = defaultdict(list)
            for handle in graphql_diagram.handles:
                handle_index[handle.node_id].append(handle)
            
            # Store handle_index in context for Node.handles() resolver
            info.context.handle_index = handle_index
            
            # Return as Strawberry type
            return GraphQLDiagram(
                nodes=graphql_diagram.nodes,
                handles=graphql_diagram.handles,
                arrows=graphql_diagram.arrows,
                persons=graphql_diagram.persons,
                api_keys=graphql_diagram.api_keys,
                metadata=graphql_diagram.metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to get diagram {diagram_id}: {e}")
            return None
    
    async def list_diagrams(
        self, 
        filter: Optional[DiagramFilterInput],
        limit: int,
        offset: int,
        info
    ) -> List[GraphQLDiagram]:
        """List diagrams with optional filtering."""
        try:
            # Get diagram service from GraphQL context
            diagram_service: DiagramService = info.context.diagram_service
            
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
                # Create metadata from file info
                metadata = DiagramMetadata(
                    id=diagram_info['path'],  # Use path as ID for loading
                    name=diagram_info['name'],
                    description=f"Format: {diagram_info['format']}, Size: {diagram_info['size']} bytes",
                    created=datetime.fromisoformat(diagram_info['modified']),  # Use modified as created for now
                    modified=datetime.fromisoformat(diagram_info['modified']),
                    version='2.0.0'
                )
                
                # Create a minimal Diagram object with just metadata
                diagram = GraphQLDiagram(
                    nodes=[],
                    handles=[],
                    arrows=[],
                    persons=[],
                    api_keys=[],
                    metadata=metadata
                )
                result.append(diagram)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list diagrams: {e}")
            return []

diagram_resolver = DiagramResolver()