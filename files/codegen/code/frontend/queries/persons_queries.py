"""Generate GraphQL queries for Person operations."""

from typing import List, Dict, Any


class PersonsQueryGenerator:
    """Generate Person related GraphQL queries."""
    
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
        """Generate all Person queries and mutations."""
        queries = []
        
        person_fields = [
            {'name': 'id'},
            {'name': 'label'},
            {'name': 'llm_config', 'fields': [
                {'name': 'service'},
                {'name': 'model'},
                {'name': 'api_key_id'},
                {'name': 'system_prompt'}
            ]},
            {'name': 'type'}
        ]
        
        # Add comment
        queries.append("# Person Queries")
        
        # GetPerson query
        field_selection = self.generate_field_selection(person_fields)
        queries.append(f"""query GetPerson($id: ID!) {{
  person(id: $id) {{
{field_selection}
  }}
}}""")
        
        # GetPersons query (note plural)
        queries.append(f"""query GetPersons($limit: Int = 100) {{
  persons(limit: $limit) {{
{field_selection}
  }}
}}""")
        
        # Add comment
        queries.append("# Person Mutations")
        
        # Generate field selection for mutations (need extra indent)
        mutation_field_selection = self.generate_field_selection(person_fields, indent=3)
        
        # CreatePerson mutation
        queries.append(f"""mutation CreatePerson($input: CreatePersonInput!) {{
  create_person(input: $input) {{
    success
    person {{
{mutation_field_selection}
    }}
    message
    error
  }}
}}""")
        
        # UpdatePerson mutation
        queries.append(f"""mutation UpdatePerson($id: ID!, $input: UpdatePersonInput!) {{
  update_person(id: $id, input: $input) {{
    success
    person {{
{mutation_field_selection}
    }}
    message
    error
  }}
}}""")
        
        # DeletePerson mutation
        queries.append("""mutation DeletePerson($id: ID!) {
  delete_person(id: $id) {
    success
    message
    error
  }
}""")
        
        return queries