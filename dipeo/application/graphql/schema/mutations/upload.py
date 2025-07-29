"""Upload mutations using UnifiedServiceRegistry."""

import logging
from typing import Optional

import strawberry
from strawberry.file_uploads import Upload

from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey
from dipeo.application.graphql.enums import DiagramFormat

from ...types.results import FileUploadResult, DiagramResult

logger = logging.getLogger(__name__)

# Service keys
FILE_SERVICE = ServiceKey("file_service")
INTEGRATED_DIAGRAM_SERVICE = ServiceKey("integrated_diagram_service")


@strawberry.type
class DiagramValidationResult:
    """Result of diagram validation."""
    success: bool
    message: Optional[str] = None
    errors: Optional[list[str]] = None
    warnings: Optional[list[str]] = None


@strawberry.type 
class DiagramConvertResult:
    """Result of diagram format conversion."""
    success: bool
    message: Optional[str] = None
    content: Optional[str] = None
    format: Optional[DiagramFormat] = None
    error: Optional[str] = None


def create_upload_mutations(registry: UnifiedServiceRegistry) -> type:
    """Create upload mutation methods with injected service registry."""
    
    @strawberry.type
    class UploadMutations:
        @strawberry.mutation
        async def upload_file(
            self, file: Upload, path: Optional[str] = None
        ) -> FileUploadResult:
            """Upload a file to the system."""
            try:
                file_service = registry.get(FILE_SERVICE.name)
                if not file_service:
                    return FileUploadResult(
                        success=False,
                        error="File service not available",
                    )
                
                # Read file content
                content = await file.read()
                
                # Determine path if not provided
                if not path:
                    path = f"uploads/{file.filename}"
                
                # Save file
                await file_service.write_file(path, content)
                
                return FileUploadResult(
                    success=True,
                    path=path,
                    size_bytes=len(content),
                    content_type=file.content_type,
                    message=f"Uploaded file: {file.filename}",
                )
                
            except Exception as e:
                logger.error(f"Failed to upload file: {e}")
                return FileUploadResult(
                    success=False,
                    error=f"Failed to upload file: {str(e)}",
                )
        
        @strawberry.mutation
        async def upload_diagram(
            self, file: Upload, format: DiagramFormat
        ) -> DiagramResult:
            """Upload and import a diagram file."""
            try:
                integrated_service = registry.require(INTEGRATED_DIAGRAM_SERVICE)
                
                # Read file content
                content = await file.read()
                content_str = content.decode('utf-8')
                
                # Convert GraphQL enum to Python enum
                format_python = format.to_python_enum()
                
                # Load and validate diagram based on format
                diagram = await integrated_service.load_from_string(
                    content=content_str,
                    format=format_python
                )
                
                # Save the diagram
                # Note: This would need actual implementation
                
                return DiagramResult(
                    success=True,
                    message=f"Uploaded diagram: {file.filename}",
                )
                
            except Exception as e:
                logger.error(f"Failed to upload diagram: {e}")
                return DiagramResult(
                    success=False,
                    error=f"Failed to upload diagram: {str(e)}",
                )
        
        @strawberry.mutation
        async def validate_diagram(
            self, content: str, format: DiagramFormat
        ) -> DiagramValidationResult:
            """Validate diagram content without saving."""
            try:
                integrated_service = registry.require(INTEGRATED_DIAGRAM_SERVICE)
                
                # Convert GraphQL enum to Python enum
                format_python = format.to_python_enum()
                
                # Validate diagram by attempting to load it
                diagram = await integrated_service.load_from_string(
                    content=content,
                    format=format_python
                )
                
                return DiagramValidationResult(
                    success=True,
                    message="Diagram is valid",
                    errors=[],
                    warnings=[],
                )
                
            except Exception as e:
                logger.error(f"Failed to validate diagram: {e}")
                return DiagramValidationResult(
                    success=False,
                    message="Validation failed",
                    errors=[str(e)],
                )
        
        @strawberry.mutation
        async def convert_diagram_format(
            self, content: str, from_format: DiagramFormat, to_format: DiagramFormat
        ) -> DiagramConvertResult:
            """Convert diagram between formats."""
            try:
                from dipeo.infra.diagram import converter_registry
                
                # Convert GraphQL enums to Python enum values (strings)
                from_format_str = from_format.to_python_enum().value
                to_format_str = to_format.to_python_enum().value
                
                # Convert diagram using the converter registry
                converted_content = converter_registry.convert(
                    content=content,
                    from_format=from_format_str,
                    to_format=to_format_str
                )
                
                return DiagramConvertResult(
                    success=True,
                    message=f"Converted from {from_format_str} to {to_format_str}",
                    content=converted_content,
                    format=to_format,
                )
                
            except Exception as e:
                logger.error(f"Failed to convert diagram: {e}")
                return DiagramConvertResult(
                    success=False,
                    error=f"Failed to convert diagram: {str(e)}",
                )
    
    return UploadMutations