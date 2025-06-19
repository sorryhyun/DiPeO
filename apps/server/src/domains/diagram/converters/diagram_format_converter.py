"""Converter for DiagramDictFormat <-> DomainDiagram conversions."""
from src.__generated__.models import DomainDiagram, DiagramDictFormat


def diagram_dict_to_graphql(diagram_dict: DiagramDictFormat) -> DomainDiagram:
    """Convert from dictionary format (internal) to GraphQL-friendly list format."""
    return DomainDiagram(
        nodes=list(diagram_dict.nodes.values()),
        handles=list(diagram_dict.handles.values()),
        arrows=list(diagram_dict.arrows.values()),
        persons=list(diagram_dict.persons.values()),
        api_keys=list(diagram_dict.api_keys.values()),
        metadata=diagram_dict.metadata
    )


def graphql_to_diagram_dict(graphql_diagram: DomainDiagram) -> DiagramDictFormat:
    """Convert from GraphQL list format back to internal dictionary format."""
    return DiagramDictFormat(
        nodes={node.id: node for node in graphql_diagram.nodes},
        handles={handle.id: handle for handle in graphql_diagram.handles},
        arrows={arrow.id: arrow for arrow in graphql_diagram.arrows},
        persons={person.id: person for person in graphql_diagram.persons},
        api_keys={api_key.id: api_key for api_key in graphql_diagram.api_keys},
        metadata=graphql_diagram.metadata
    )