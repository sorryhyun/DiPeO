"""Converter for BackendDiagram <-> DomainDiagram conversions."""

from dipeo_domain import DomainDiagram

from dipeo_server.domains.diagram.services.models import BackendDiagram


def backend_to_graphql(diagram_dict: BackendDiagram) -> DomainDiagram:
    """Convert from dictionary format (internal) to GraphQL-friendly list format."""
    # Add IDs to each item from the dictionary keys
    nodes = []
    for node_id, node_data in diagram_dict.nodes.items():
        node_with_id = dict(node_data) if isinstance(node_data, dict) else node_data
        if isinstance(node_with_id, dict) and "id" not in node_with_id:
            node_with_id["id"] = node_id
        nodes.append(node_with_id)

    handles = []
    for handle_id, handle_data in diagram_dict.handles.items():
        handle_with_id = (
            dict(handle_data) if isinstance(handle_data, dict) else handle_data
        )
        if isinstance(handle_with_id, dict) and "id" not in handle_with_id:
            handle_with_id["id"] = handle_id
        handles.append(handle_with_id)

    arrows = []
    for arrow_id, arrow_data in diagram_dict.arrows.items():
        arrow_with_id = dict(arrow_data) if isinstance(arrow_data, dict) else arrow_data
        if isinstance(arrow_with_id, dict) and "id" not in arrow_with_id:
            arrow_with_id["id"] = arrow_id
        arrows.append(arrow_with_id)

    persons = []
    for person_id, person_data in diagram_dict.persons.items():
        person_with_id = (
            dict(person_data) if isinstance(person_data, dict) else person_data
        )
        if isinstance(person_with_id, dict) and "id" not in person_with_id:
            person_with_id["id"] = person_id
        persons.append(person_with_id)

    api_keys = []
    for api_key_id, api_key_data in diagram_dict.api_keys.items():
        api_key_with_id = (
            dict(api_key_data) if isinstance(api_key_data, dict) else api_key_data
        )
        if isinstance(api_key_with_id, dict) and "id" not in api_key_with_id:
            api_key_with_id["id"] = api_key_id
        api_keys.append(api_key_with_id)

    return DomainDiagram(
        nodes=nodes,
        handles=handles,
        arrows=arrows,
        persons=persons,
        api_keys=api_keys,
        metadata=diagram_dict.metadata,
    )


def graphql_to_backend(graphql_diagram: DomainDiagram) -> BackendDiagram:
    return BackendDiagram(
        nodes={node.id: node for node in graphql_diagram.nodes},
        handles={handle.id: handle for handle in graphql_diagram.handles},
        arrows={arrow.id: arrow for arrow in graphql_diagram.arrows},
        persons={person.id: person for person in graphql_diagram.persons},
        api_keys={api_key.id: api_key for api_key in graphql_diagram.api_keys},
        metadata=graphql_diagram.metadata,
    )
