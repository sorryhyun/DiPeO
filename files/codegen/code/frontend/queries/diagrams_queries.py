"""Generate GraphQL queries for Diagram operations."""

from typing import List, Dict, Any


class DiagramsQueryGenerator:
    """Generate Diagram related GraphQL queries."""
    
    def generate_field_selection(self, fields: List[Dict[str, Any]], indent: int = 2) -> str:
        """Generate GraphQL field selection syntax."""
        lines = []
        indent_str = "  " * indent
        
        for field in fields:
            if field.get('fields'):
                # Nested field
                lines.append(f"{indent_str}{field['name']} {{")
                lines.append(self.generate_field_selection(field['fields'], indent + 1))
                lines.append(f"{indent_str}}}")
            else:
                # Simple field
                lines.append(f"{indent_str}{field['name']}")
        
        return "\n".join(lines)
    
    def generate(self) -> List[str]:
        """Generate all Diagram queries and mutations."""
        queries = []
        
        # Fields for GetDiagram query
        diagram_fields = [
            {'name': 'nodes', 'fields': [
                {'name': 'id'},
                {'name': 'type'},
                {'name': 'position', 'fields': [
                    {'name': 'x'},
                    {'name': 'y'}
                ]},
                {'name': 'data'}
            ]},
            {'name': 'handles', 'fields': [
                {'name': 'id'},
                {'name': 'node_id'},
                {'name': 'label'},
                {'name': 'direction'},
                {'name': 'data_type'},
                {'name': 'position'}
            ]},
            {'name': 'arrows', 'fields': [
                {'name': 'id'},
                {'name': 'source'},
                {'name': 'target'},
                {'name': 'content_type'},
                {'name': 'label'},
                {'name': 'data'}
            ]},
            {'name': 'persons', 'fields': [
                {'name': 'id'},
                {'name': 'label'},
                {'name': 'llm_config', 'fields': [
                    {'name': 'service'},
                    {'name': 'model'},
                    {'name': 'api_key_id'},
                    {'name': 'system_prompt'}
                ]},
                {'name': 'type'}
            ]},
            {'name': 'metadata', 'fields': [
                {'name': 'id'},
                {'name': 'name'},
                {'name': 'description'},
                {'name': 'version'},
                {'name': 'created'},
                {'name': 'modified'},
                {'name': 'author'},
                {'name': 'tags'}
            ]}
        ]
        
        # Fields for ListDiagrams query
        list_fields = [
            {'name': 'metadata', 'fields': [
                {'name': 'id'},
                {'name': 'name'},
                {'name': 'description'},
                {'name': 'author'},
                {'name': 'created'},
                {'name': 'modified'},
                {'name': 'tags'}
            ]},
            {'name': 'nodeCount'},
            {'name': 'arrowCount'}
        ]
        
        # Add comment
        queries.append("# Diagram Queries")
        
        # GetDiagram query
        field_selection = self.generate_field_selection(diagram_fields)
        queries.append(f"""query GetDiagram($id: ID!) {{
  diagram(id: $id) {{
{field_selection}
  }}
}}""")
        
        # ListDiagrams query
        list_field_selection = self.generate_field_selection(list_fields)
        queries.append(f"""query ListDiagrams($filter: DiagramFilterInput, $limit: Int, $offset: Int) {{
  diagrams(filter: $filter, limit: $limit, offset: $offset) {{
{list_field_selection}
  }}
}}""")
        
        # Add comment
        queries.append("# Diagram Mutations")
        
        # CreateDiagram mutation
        queries.append("""mutation CreateDiagram($input: CreateDiagramInput!) {
  create_diagram(input: $input) {
    success
    diagram {
      metadata {
        id
        name
      }
    }
    message
    error
  }
}""")
        
        # ExecuteDiagram mutation
        queries.append("""mutation ExecuteDiagram($input: ExecuteDiagramInput!) {
  execute_diagram(input: $input) {
    success
    execution {
      id
    }
    message
    error
  }
}""")
        
        # DeleteDiagram mutation
        queries.append("""mutation DeleteDiagram($id: ID!) {
  delete_diagram(id: $id) {
    success
    message
    error
  }
}""")
        
        return queries