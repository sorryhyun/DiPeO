"""Generate GraphQL queries for Execution operations."""

from typing import List, Dict, Any


class ExecutionsQueryGenerator:
    """Generate Execution related GraphQL queries."""
    
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
        """Generate all Execution queries and mutations."""
        queries = []
        
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
        
        # Add comment
        queries.append("# Execution Queries")
        
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
        
        # ExecutionOrder query
        queries.append("""query ExecutionOrder($executionId: ID!) {
  execution_order(execution_id: $executionId)
}""")
        
        # Add comment
        queries.append("# Execution Subscriptions")
        
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
        
        # Add comment
        queries.append("# Execution Mutations")
        
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
        
        return queries