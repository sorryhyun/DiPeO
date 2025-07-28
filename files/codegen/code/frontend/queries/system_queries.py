"""Generate GraphQL queries for System operations."""

from typing import List


class SystemQueryGenerator:
    """Generate System related GraphQL queries."""
    
    def generate(self) -> List[str]:
        """Generate all System queries."""
        queries = []
        
        # Add comment
        queries.append("# System Queries")
        
        # GetSystemInfo query
        queries.append("""query GetSystemInfo {
  system_info
}""")
        
        queries.append("")  # Empty line at end
        
        return queries