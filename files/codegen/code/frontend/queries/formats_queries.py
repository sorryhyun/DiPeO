"""Generate GraphQL queries for Format operations."""

from typing import List


class FormatsQueryGenerator:
    """Generate Format related GraphQL queries."""
    
    def generate(self) -> List[str]:
        """Generate all Format queries."""
        queries = []
        
        # Add comment
        queries.append("# Format Queries")
        
        # GetSupportedFormats query
        queries.append("""query GetSupportedFormats {
  supported_formats {
    format
    name
    extension
    supports_export
    supports_import
    description
  }
}""")
        
        return queries