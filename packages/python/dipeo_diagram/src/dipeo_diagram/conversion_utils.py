"""Conversion utilities for diagram formats."""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from dipeo_domain import DomainDiagram

if TYPE_CHECKING:
    from .models import BackendDiagram


def backend_to_graphql(backend_dict: "BackendDiagram") -> DomainDiagram:
    """Convert backend dict representation to GraphQL domain model.

    The backend representation uses dicts of dicts for efficient lookup.
    The GraphQL representation uses lists for easier client handling.
    """
    # Convert dict-of-dicts to lists (if necessary)
    def ensure_list(obj):
        if obj is None:
            return []
        if isinstance(obj, dict):
            return list(obj.values())
        return obj

    # Special handling for handles to ensure 'id' field exists
    def ensure_handles_list(handles_dict):
        if handles_dict is None:
            return []
        if isinstance(handles_dict, dict):
            result = []
            for key, value in handles_dict.items():
                if isinstance(value, dict) and 'id' not in value:
                    # Add the key as id if missing
                    handle = value.copy()
                    handle['id'] = key
                    result.append(handle)
                else:
                    result.append(value)
            return result
        return handles_dict

    # Create a copy to avoid mutating the original
    result_dict = {
        "nodes": ensure_list(backend_dict.nodes),
        "arrows": ensure_list(backend_dict.arrows),
        "handles": ensure_handles_list(backend_dict.handles),
        "persons": ensure_list(backend_dict.persons),
        "apiKeys": ensure_list(backend_dict.api_keys),
        "metadata": backend_dict.metadata,
    }

    # Remove None values
    result_dict = {k: v for k, v in result_dict.items() if v is not None}

    return DomainDiagram(**result_dict)


def graphql_to_backend(graphql_diagram: DomainDiagram) -> dict[str, dict[str, Any]]:
    """Convert GraphQL domain model to backend dict representation.

    The backend representation uses dicts of dicts for efficient lookup.
    The GraphQL representation uses lists for easier client handling.
    """

    def list_to_dict(items, id_attr="id"):
        if items is None:
            return {}
        # If already a dict, return as-is
        if isinstance(items, Mapping):
            return dict(items)
        # Convert list to dict using ID
        result = {}
        for item in items:
            # Handle both dict and object representations
            if hasattr(item, "__dict__"):
                item_dict = item.__dict__
                item_id = getattr(item, id_attr)
            else:
                item_dict = item
                item_id = item.get(id_attr)

            if item_id:
                result[item_id] = item_dict

        return result

    # Build the backend dict structure
    return {
        "nodes": list_to_dict(graphql_diagram.nodes),
        "arrows": list_to_dict(graphql_diagram.arrows),
        "handles": list_to_dict(graphql_diagram.handles),
        "persons": list_to_dict(graphql_diagram.persons),
        "api_keys": list_to_dict(graphql_diagram.apiKeys),
        "metadata": graphql_diagram.metadata or {},
    }