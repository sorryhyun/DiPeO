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
        queries.append("""mutation UploadFile($file: Upload!, $path: String) {
  upload_file(file: $file, path: $path) {
    success
    path
    size_bytes
    content_type
    message
    error
  }
}""")
        
        # ValidateDiagram mutation
        queries.append("""mutation ValidateDiagram($content: String!, $format: DiagramFormat!) {
  validate_diagram(content: $content, format: $format) {
    success
    message
    errors
    warnings
  }
}""")
        
        # ConvertDiagram mutation
        queries.append("""mutation ConvertDiagramFormat($content: String!, $fromFormat: DiagramFormat!, $toFormat: DiagramFormat!) {
  convert_diagram_format(content: $content, from_format: $fromFormat, to_format: $toFormat) {
    success
    message
    error
    content
    format
    format
  }
}""")
        
        return queries