"""Combined GraphQL mutations."""

import strawberry

from dipeo.application.registry import ServiceRegistry

from .mutations import (
    create_diagram_mutations,
    create_execution_mutations,
    create_person_mutations,
    create_api_key_mutations,
    create_node_mutations,
    create_upload_mutations,
    create_cli_session_mutations,
)


def create_mutation_type(registry: ServiceRegistry) -> type:
    """Create a combined Mutation type with all mutation categories."""
    
    # Create individual mutation classes
    DiagramMutations = create_diagram_mutations(registry)
    ExecutionMutations = create_execution_mutations(registry)
    PersonMutations = create_person_mutations(registry)
    ApiKeyMutations = create_api_key_mutations(registry)
    NodeMutations = create_node_mutations(registry)
    UploadMutations = create_upload_mutations(registry)
    CliSessionMutations = create_cli_session_mutations(registry)
    
    # Combine into single Mutation class
    @strawberry.type
    class Mutation(
        DiagramMutations,
        ExecutionMutations,
        PersonMutations,
        ApiKeyMutations,
        NodeMutations,
        UploadMutations,
        CliSessionMutations,
    ):
        """Combined GraphQL mutation type."""
        pass
    
    return Mutation