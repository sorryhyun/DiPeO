"""Combined GraphQL mutations."""

import strawberry

from dipeo.application.registry import ServiceRegistry

from .mutations import (
    create_api_key_mutations,
    create_cli_session_mutations,
    create_diagram_mutations,
    create_execution_mutations,
    create_node_mutations,
    create_person_mutations,
    create_upload_mutations,
)


def create_mutation_type(registry: ServiceRegistry) -> type:
    """Create combined Mutation type with all mutation categories."""
    diagram_mutations = create_diagram_mutations(registry)
    execution_mutations = create_execution_mutations(registry)
    person_mutations = create_person_mutations(registry)
    api_key_mutations = create_api_key_mutations(registry)
    node_mutations = create_node_mutations(registry)
    upload_mutations = create_upload_mutations(registry)
    cli_session_mutations = create_cli_session_mutations(registry)

    @strawberry.type
    class Mutation(
        diagram_mutations,
        execution_mutations,
        person_mutations,
        api_key_mutations,
        node_mutations,
        upload_mutations,
        cli_session_mutations,
    ):
        pass

    return Mutation
