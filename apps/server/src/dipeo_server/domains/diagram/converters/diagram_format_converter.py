"""Converter for BackendDiagram <-> DomainDiagram conversions."""

from dipeo_domain import DomainDiagram
from ..services.models import BackendDiagram

from collections.abc import Mapping
from typing import Any, Dict, List

FIELD_NAMES = ("nodes", "handles", "arrows", "persons", "api_keys")  # attrs on BackendDiagram


def _dict_to_list(mapping: Dict[str, Any]) -> List[Any]:
    """Convert a {id: obj} mapping to a list[dict], adding missing 'id' fields."""
    return [
        ({**value, "id": key} if isinstance(value, Mapping) and "id" not in value else value)
        for key, value in mapping.items()
    ]

def backend_to_graphql(diagram: BackendDiagram) -> DomainDiagram:
    data = {name: _dict_to_list(getattr(diagram, name)) for name in FIELD_NAMES}
    data["metadata"] = diagram.metadata
    return DomainDiagram(**data)


def graphql_to_backend(graphql_diagram: DomainDiagram) -> BackendDiagram:
    return BackendDiagram(
        nodes={node.id: node for node in graphql_diagram.nodes},
        handles={handle.id: handle for handle in graphql_diagram.handles},
        arrows={arrow.id: arrow for arrow in graphql_diagram.arrows},
        persons={person.id: person for person in graphql_diagram.persons},
        api_keys={api_key.id: api_key for api_key in graphql_diagram.api_keys},
        metadata=graphql_diagram.metadata,
    )
