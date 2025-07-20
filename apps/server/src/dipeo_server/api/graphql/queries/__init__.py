"""GraphQL queries module - combines all query methods."""

import strawberry

# FilterInput types are now in generated_types.py

# Import query methods from individual files
# Generated queries (disabled - managed through Diagram)
# from ..generated.queries.person_queries import person, Persons  # Disabled - managed through Diagram
# from ..generated.queries.node_queries import node, Nodes  # Disabled - managed through Diagram
# from ..generated.queries.handle_queries import handle, Handles  # Disabled - managed through Diagram
# from ..generated.queries.arrow_queries import arrow, Arrows  # Disabled - managed through Diagram

# Generated queries (active)
from ..generated.queries.apikey_queries import apikey, ApiKeys

# Custom queries
from ..custom.queries.diagram_queries import diagram, Diagrams
from ..custom.queries.execution_queries import execution, Executions
from ..custom.queries.system_queries import (
    system_info,
    execution_capabilities,
    health,
    conversations,
    supported_formats,
    execution_order,
    prompt_files,
    prompt_file,
    schema_enums,
    SchemaEnums,
)

# Additional imports for backward compatibility
from dipeo_server.api.graphql.generated.types import (
    ApiKeyID,
)


@strawberry.type
class Query:
    """Combined GraphQL query type."""
    
    # Entity queries
    # person = person  # Disabled - managed through Diagram
    # persons = Persons  # Disabled - managed through Diagram
    
    # node = node  # Disabled - managed through Diagram
    # nodes = Nodes  # Disabled - managed through Diagram
    
    diagram = diagram
    diagrams = Diagrams
    
    # diagraminfo = diagraminfo  # TODO: Fix DiagramInfo model import
    # diagram_infos = DiagramInfos  # TODO: Fix DiagramInfo model import
    
    execution = execution
    executions = Executions
    
    # handle = handle  # Disabled - managed through Diagram
    # handles = Handles  # Disabled - managed through Diagram
    
    # arrow = arrow  # Disabled - managed through Diagram
    # arrows = Arrows  # Disabled - managed through Diagram
    
    api_key = apikey
    api_keys = ApiKeys
    
    # System queries
    system_info = system_info
    execution_capabilities = execution_capabilities
    health = health
    conversations = conversations
    supported_formats = supported_formats
    execution_order = execution_order
    prompt_files = prompt_files
    prompt_file = prompt_file
    schema_enums = schema_enums
    
    
    # Additional legacy query
    @strawberry.field
    async def available_models(
        self, service: str, api_key_id: ApiKeyID, info
    ) -> list[str]:
        """Get available models for a specific service and API key."""
        from dipeo_server.api.graphql.resolvers.api_key import api_key_resolver
        return await api_key_resolver.get_available_models(service, api_key_id, info)


__all__ = ["Query"]