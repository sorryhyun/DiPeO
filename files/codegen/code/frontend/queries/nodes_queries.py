"""Generate GraphQL queries for Node operations."""

from typing import List


class NodesQueryGenerator:
    """Generate Node related GraphQL queries."""
    
    def generate(self) -> List[str]:
        """Generate all Node mutations."""
        queries = []
        
        # Add comment
        queries.append("# Node Mutations")
        
        # CreateNode mutation
        queries.append("""mutation CreateNode($diagramId: ID!, $input: CreateNodeInput!) {
  create_node(diagram_id: $diagramId, input: $input) {
    success
    node {
      id
      type
      position {
        x
        y
      }
      data
    }
    message
    error
  }
}""")
        
        # UpdateNode mutation
        queries.append("""mutation UpdateNode($diagramId: ID!, $nodeId: ID!, $input: UpdateNodeInput!) {
  update_node(diagram_id: $diagramId, node_id: $nodeId, input: $input) {
    success
    node {
      id
      type
      position {
        x
        y
      }
      data
    }
    message
    error
  }
}""")
        
        # DeleteNode mutation
        queries.append("""mutation DeleteNode($diagramId: ID!, $nodeId: ID!) {
  delete_node(diagram_id: $diagramId, node_id: $nodeId) {
    success
    message
    error
  }
}""")
        
        queries.append("")  # Empty line at end
        
        return queries