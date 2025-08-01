"""Generate GraphQL queries following DiPeO's actual patterns."""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import specific query generators
from ..queries import (
    ApiKeysQueryGenerator,
    FilesQueryGenerator,
    FormatsQueryGenerator,
    NodesQueryGenerator,
    SystemQueryGenerator,
    PromptsQueryGenerator,
    ConversationsQueryGenerator
)


class DiPeOQueryGenerator:
    """Generate GraphQL query files following DiPeO conventions."""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    def generate_mutation_response_fields(self, entity: str, fields: List[Dict[str, Any]]) -> str:
        """Generate standard mutation response fields."""
        entity_lower = entity.lower()
        field_selection = self.generate_field_selection(fields, indent=2)
        
        return f"""  success
  {entity_lower} {{
{field_selection}
  }}
  message
  error"""
    
    def generate_diagram_queries(self):
        """Generate queries for Diagram entity."""
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
        
        queries = []
        
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
        
        # CreateDiagram mutation
        queries.append(f"""mutation CreateDiagram($input: CreateDiagramInput!) {{
  create_diagram(input: $input) {{
    success
    diagram {{
      metadata {{
        id
        name
      }}
    }}
    message
    error
  }}
}}""")
        
        # ExecuteDiagram mutation
        queries.append(f"""mutation ExecuteDiagram($input: ExecuteDiagramInput!) {{
  execute_diagram(input: $input) {{
    success
    execution {{
      id
    }}
    message
    error
  }}
}}""")
        
        # DeleteDiagram mutation
        queries.append(f"""mutation DeleteDiagram($id: ID!) {{
  delete_diagram(id: $id) {{
    success
    message
    error
  }}
}}""")
        
        self.write_query_file('diagrams', queries)
    
    def generate_person_queries(self):
        """Generate queries for Person entity."""
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
        
        queries = []
        
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
        queries.append(f"""mutation DeletePerson($id: ID!) {{
  delete_person(id: $id) {{
    success
    message
    error
  }}
}}""")
        
        
        self.write_query_file('persons', queries)
    
    def generate_execution_queries(self):
        """Generate queries for Execution entity."""
        # Full execution fields
        full_fields = [
            {'name': 'id'},
            {'name': 'status'},
            {'name': 'diagram_id'},
            {'name': 'started_at'},
            {'name': 'ended_at'},
            {'name': 'node_states'},
            {'name': 'node_outputs'},
            {'name': 'variables'},
            {'name': 'token_usage', 'fields': [
                {'name': 'input'},
                {'name': 'output'},
                {'name': 'cached'}
            ]},
            {'name': 'error'},
            {'name': 'duration_seconds'},
            {'name': 'is_active'}
        ]
        
        # List fields (subset)
        list_fields = [
            {'name': 'id'},
            {'name': 'status'},
            {'name': 'diagram_id'},
            {'name': 'started_at'},
            {'name': 'ended_at'},
            {'name': 'is_active'},
            {'name': 'duration_seconds'}
        ]
        
        # Update fields (for subscription)
        update_fields = [
            {'name': 'execution_id'},
            {'name': 'event_type'},
            {'name': 'data'},
            {'name': 'timestamp'}
        ]
        
        queries = []
        
        # GetExecution query
        field_selection = self.generate_field_selection(full_fields)
        queries.append(f"""query GetExecution($id: ID!) {{
  execution(id: $id) {{
{field_selection}
  }}
}}""")
        
        # ListExecutions query
        list_field_selection = self.generate_field_selection(list_fields)
        queries.append(f"""query ListExecutions($filter: ExecutionFilterInput, $limit: Int, $offset: Int) {{
  executions(filter: $filter, limit: $limit, offset: $offset) {{
{list_field_selection}
  }}
}}""")
        
        # ExecutionUpdates subscription
        update_field_selection = self.generate_field_selection(update_fields)
        queries.append(f"""subscription ExecutionUpdates($executionId: ID!) {{
  execution_updates(execution_id: $executionId) {{
{update_field_selection}
  }}
}}""")
        
        # NodeUpdates subscription
        queries.append("""subscription NodeUpdates($executionId: ID!, $nodeId: String) {
  node_updates(execution_id: $executionId, node_id: $nodeId)
}""")
        
        # InteractivePrompts subscription
        queries.append("""subscription InteractivePrompts($executionId: ID!) {
  interactive_prompts(execution_id: $executionId)
}""")
        
        # ControlExecution mutation
        queries.append("""mutation ControlExecution($input: ExecutionControlInput!) {
  control_execution(input: $input) {
    success
    execution {
      id
      status
    }
    message
    error
  }
}""")
        
        # SendInteractiveResponse mutation
        queries.append("""mutation SendInteractiveResponse($input: InteractiveResponseInput!) {
  send_interactive_response(input: $input) {
    success
    execution {
      id
      status
      node_states
    }
    message
    error
  }
}""")
        
        # ExecutionOrder query
        queries.append("""query ExecutionOrder($executionId: ID!) {
  execution_order(execution_id: $executionId)
}""")
        
        self.write_query_file('executions', queries)
    
    def write_query_file(self, entity: str, queries: List[str]):
        """Write queries to a GraphQL file."""
        filename = f"{entity}.graphql"
        filepath = self.output_dir / filename
        
        # Join queries with double newlines, but handle comments differently
        formatted_queries = []
        for i, query in enumerate(queries):
            if query.startswith('#'):
                # Comment - add extra newline before (except first)
                if i > 0:
                    formatted_queries.append("")
                formatted_queries.append(query)
            else:
                formatted_queries.append(query)
                # Add blank line after each query/mutation (except last)
                if i < len(queries) - 1 and not queries[i + 1].startswith('#'):
                    formatted_queries.append("")
        
        content = "\n".join(formatted_queries)
        
        with open(filepath, 'w') as f:
            f.write(content)
            f.write("\n")  # Ensure file ends with newline
        
        print(f"Generated {filepath}")
    
    def generate_all_queries(self):
        """Generate queries for all entities."""
        # Generate core entity queries
        self.generate_diagram_queries()
        self.generate_person_queries()
        self.generate_execution_queries()
        
        # Generate additional queries using specific generators
        # API Keys
        api_keys_generator = ApiKeysQueryGenerator()
        self.write_query_file('apiKeys', api_keys_generator.generate())
        
        # Files
        files_generator = FilesQueryGenerator()
        self.write_query_file('files', files_generator.generate())
        
        # Formats
        formats_generator = FormatsQueryGenerator()
        self.write_query_file('formats', formats_generator.generate())
        
        # Nodes
        nodes_generator = NodesQueryGenerator()
        self.write_query_file('nodes', nodes_generator.generate())
        
        # System
        system_generator = SystemQueryGenerator()
        self.write_query_file('system', system_generator.generate())
        
        # Prompts
        prompts_generator = PromptsQueryGenerator()
        self.write_query_file('prompts', prompts_generator.generate())
        
        # Conversations
        conversations_generator = ConversationsQueryGenerator()
        self.write_query_file('conversations', conversations_generator.generate())
        
        print(f"\nAll GraphQL queries generated successfully in {self.output_dir}")


def main():
    """Main entry point for query generation."""
    import sys
    
    # Default output directory for GraphQL queries
    output_dir = '/home/soryhyun/DiPeO/apps/web/src/__generated__/queries'
    
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    
    generator = DiPeOQueryGenerator(output_dir)
    generator.generate_all_queries()


if __name__ == "__main__":
    main()