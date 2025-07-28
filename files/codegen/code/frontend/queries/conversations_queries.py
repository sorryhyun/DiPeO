"""Generate GraphQL queries for Conversation operations."""

from typing import List


class ConversationsQueryGenerator:
    """Generate Conversation related GraphQL queries."""
    
    def generate(self) -> List[str]:
        """Generate all Conversation queries and mutations."""
        queries = []
        
        # Add comment
        queries.append("# Conversation Queries")
        
        # GetConversations query
        queries.append("""query GetConversations(
  $person_id: PersonID
  $execution_id: ExecutionID
  $search: String
  $show_forgotten: Boolean = false
  $limit: Int = 100
  $offset: Int = 0
  $since: DateTime
) {
  conversations(
    person_id: $person_id
    execution_id: $execution_id
    search: $search
    show_forgotten: $show_forgotten
    limit: $limit
    offset: $offset
    since: $since
  )
}""")
        
        # Add comment
        queries.append("# Conversation Mutations")
        
        # ClearConversations mutation
        queries.append("""mutation ClearConversations {
  clear_conversations {
    success
    message
  }
}""")
        
        return queries