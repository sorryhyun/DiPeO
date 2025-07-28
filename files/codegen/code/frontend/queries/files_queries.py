"""Generate GraphQL queries for File operations."""

from typing import List


class FilesQueryGenerator:
    """Generate File related GraphQL queries."""
    
    def generate(self) -> List[str]:
        """Generate all File queries and mutations."""
        queries = []
        
        # Add comment
        queries.append("# File Operations")
        queries.append("")
        
        # UploadFile mutation
        queries.append("""mutation UploadFile($file: Upload!, $category: String! = "general") {
  upload_file(file: $file, category: $category) {
    success
    path
    size_bytes
    content_type
    message
    error
  }
}""")
        
        # ValidateDiagram mutation
        queries.append("""mutation ValidateDiagram($diagramContent: JSONScalar!) {
  validate_diagram(diagram_content: $diagramContent) {
    is_valid
    errors
    node_count
    arrow_count
    person_count
  }
}""")
        
        # ConvertDiagram mutation
        queries.append("""mutation ConvertDiagram($content: JSONScalar!, $targetFormat: DiagramFormat = NATIVE, $includeMetadata: Boolean = true) {
  convert_diagram(content: $content, target_format: $targetFormat, include_metadata: $includeMetadata) {
    success
    message
    error
    content
    format
    filename
  }
}""")
        
        return queries