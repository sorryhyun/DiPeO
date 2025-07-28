"""Generate GraphQL queries for Prompt operations."""

from typing import List


class PromptsQueryGenerator:
    """Generate Prompt related GraphQL queries."""
    
    def generate(self) -> List[str]:
        """Generate all Prompt queries."""
        queries = []
        
        # GetPromptFiles query
        queries.append("""query GetPromptFiles {
  prompt_files
}""")
        
        # GetPromptFile query
        queries.append("""query GetPromptFile($filename: String!) {
  prompt_file(filename: $filename)
}""")
        
        return queries