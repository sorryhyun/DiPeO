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
        queries.append("""mutation CreateNode($diagramId: DiagramID!, $inputData: CreateNodeInput!) {
  create_node(diagram_id: $diagramId, input_data: $inputData) {
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
        queries.append("""mutation UpdateNode($inputData: UpdateNodeInput!) {
  update_node(input_data: $inputData) {
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
        queries.append("""mutation DeleteNode($nodeId: NodeID!) {
  delete_node(node_id: $nodeId) {
    success
    message
    error
  }
}""")
        
        queries.append("")  # Empty line at end
        
        return queries