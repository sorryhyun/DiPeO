"""GraphQL schema generator module."""

from .graphql_schema_generator import (
    combine_node_data_ast,
    extract_graphql_types,
    prepare_template_data,
    render_graphql_schema,
    generate_summary,
    # Backward compatibility
    main
)

__all__ = [
    'combine_node_data_ast',
    'extract_graphql_types',
    'prepare_template_data',
    'render_graphql_schema',
    'generate_summary',
    'main'
]