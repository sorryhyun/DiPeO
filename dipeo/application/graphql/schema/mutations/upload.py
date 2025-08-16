"""Upload mutations using ServiceRegistry."""

import logging
from typing import Optional

import strawberry
from strawberry.file_uploads import Upload

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER, DIAGRAM_SERVICE
from dipeo.application.graphql.enums import DiagramFormat
from dipeo.core.constants import FILES_DIR

from ...types.results import FileUploadResult, DiagramResult

logger = logging.getLogger(__name__)


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


def create_upload_mutations(registry: ServiceRegistry) -> type:
    """Create upload mutation methods with injected service registry."""
    
    @strawberry.type
    class UploadMutations:
        @strawberry.mutation
        async def upload_file(
            self, file: Upload, path: Optional[str] = None
        ) -> FileUploadResult:
            """Upload a file to the system."""
            try:
                filesystem = registry.get(FILESYSTEM_ADAPTER)
                if not filesystem:
                    return FileUploadResult(
                        success=False,
                        error="Filesystem adapter not available",
                    )
                
                # Read file content
                content = await file.read()
                
                # Determine path if not provided
                if not path:
                    path = f"uploads/{file.filename}"
                
                # Split path into directory and filename
                from pathlib import Path
                base_dir = Path(FILES_DIR)
                path_obj = Path(path)
                
                # Create full path
                full_path = base_dir / path_obj
                parent_dir = full_path.parent
                
                # Create parent directory if needed
                if not filesystem.exists(parent_dir):
                    filesystem.mkdir(parent_dir, parents=True)
                
                # Check if this is a diagram file based on extension
                is_diagram_file = path_obj.name.endswith(('.json', '.yaml', '.yml', 
                                                         '.native.json', '.light.yaml', 
                                                         '.readable.yaml'))
                
                # Create backup if needed and file exists
                if not is_diagram_file and filesystem.exists(full_path):
                    import time
                    timestamp = int(time.time())
                    backup_path = full_path.parent / f"{full_path.stem}.{timestamp}.backup{full_path.suffix}"
                    
                    # Read existing content and write backup
                    with filesystem.open(full_path, "rb") as src:
                        with filesystem.open(backup_path, "wb") as dst:
                            dst.write(src.read())
                
                # Write the file
                with filesystem.open(full_path, "wb") as f:
                    f.write(content)
                
                # Get relative path for response
                relative_path = str(full_path.relative_to(base_dir))
                
                return FileUploadResult(
                    success=True,
                    path=relative_path,
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
                integrated_service = registry.resolve(DIAGRAM_SERVICE)
                
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
                integrated_service = registry.resolve(DIAGRAM_SERVICE)
                
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
                from dipeo.infrastructure.services.diagram import converter_registry
                
                # Convert GraphQL enums to Python enum values (strings)
                from_format_str = from_format.to_python_enum().value
                to_format_str = to_format.to_python_enum().value
                
                # Initialize converter if needed
                if not converter_registry._initialized:
                    await converter_registry.initialize()
                
                # Convert diagram using deserialize then serialize
                diagram = converter_registry.deserialize(content, from_format_str)
                converted_content = converter_registry.serialize(diagram, to_format_str)
                
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