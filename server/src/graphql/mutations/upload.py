"""
GraphQL mutations for file upload support.

Implements the GraphQL multipart request specification:
https://github.com/jaydenseric/graphql-multipart-request-spec
"""

import strawberry
from strawberry.file_uploads import Upload
from typing import Optional, List
import yaml
import json
from pathlib import Path
import uuid
import logging

from ...services.diagram_service import DiagramService
from ...models.domain import DiagramMetadata
from ..context import Context

logger = logging.getLogger(__name__)

@strawberry.type
class FileUploadResult:
    """Result of a file upload operation."""
    success: bool
    message: str
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None

@strawberry.type
class DiagramUploadResult:
    """Result of a diagram file upload."""
    success: bool
    message: str
    diagram_id: Optional[str] = None
    diagram_name: Optional[str] = None
    node_count: Optional[int] = None

@strawberry.type
class UploadMutations:
    """File upload mutations for DiPeO."""
    
    @strawberry.mutation
    async def upload_file(
        self,
        file: Upload,
        category: str = "general",
        info: strawberry.Info = None
    ) -> FileUploadResult:
        """
        Upload a general file to the server.
        
        Args:
            file: The file to upload (via multipart form)
            category: Category for organizing uploads (general, images, data, etc.)
            info: GraphQL context info
            
        Returns:
            FileUploadResult with upload details
        """
        try:
            # Read file info
            filename = file.filename
            file_content = await file.read()
            file_size = len(file_content)
            
            # Validate file size (10MB limit)
            if file_size > 10 * 1024 * 1024:
                return FileUploadResult(
                    success=False,
                    message="File size exceeds 10MB limit"
                )
            
            # Create upload directory
            upload_base = Path("files/uploads")
            category_dir = upload_base / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            file_id = f"{uuid.uuid4().hex[:8]}_{filename}"
            file_path = category_dir / file_id
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Determine file type
            file_ext = Path(filename).suffix.lower()
            file_type = "unknown"
            if file_ext in ['.json', '.yaml', '.yml']:
                file_type = "diagram"
            elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                file_type = "image"
            elif file_ext in ['.csv', '.txt', '.log']:
                file_type = "data"
            
            logger.info(f"File uploaded: {filename} -> {file_path} (size: {file_size} bytes)")
            
            return FileUploadResult(
                success=True,
                message=f"File '{filename}' uploaded successfully",
                file_id=file_id,
                file_path=str(file_path),
                file_type=file_type,
                file_size=file_size
            )
            
        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            return FileUploadResult(
                success=False,
                message=f"Upload failed: {str(e)}"
            )
    
    @strawberry.mutation
    async def upload_diagram(
        self,
        file: Upload,
        info: strawberry.Info = None
    ) -> DiagramUploadResult:
        """
        Upload and import a diagram file (JSON or YAML).
        
        Args:
            file: The diagram file to upload
            info: GraphQL context info
            
        Returns:
            DiagramUploadResult with diagram details
        """
        context: Context = info.context
        
        try:
            # Read file
            filename = file.filename
            file_content = await file.read()
            
            # Validate file size (5MB limit for diagrams)
            if len(file_content) > 5 * 1024 * 1024:
                return DiagramUploadResult(
                    success=False,
                    message="Diagram file exceeds 5MB limit"
                )
            
            # Parse diagram based on file extension
            file_ext = Path(filename).suffix.lower()
            
            if file_ext in ['.yaml', '.yml']:
                diagram_data = yaml.safe_load(file_content.decode('utf-8'))
            elif file_ext == '.json':
                diagram_data = json.loads(file_content.decode('utf-8'))
            else:
                return DiagramUploadResult(
                    success=False,
                    message=f"Unsupported file type: {file_ext}. Use .json or .yaml"
                )
            
            # Validate it's a diagram
            if not isinstance(diagram_data, dict) or 'nodes' not in diagram_data:
                return DiagramUploadResult(
                    success=False,
                    message="Invalid diagram format: missing 'nodes' field"
                )
            
            # Save via diagram service
            diagram_id = await context.diagram_service.save_diagram(diagram_data, filename)
            
            # Get diagram info
            saved_diagram = await context.diagram_service.get_diagram(diagram_id)
            
            logger.info(f"Diagram uploaded: {filename} -> {diagram_id}")
            
            return DiagramUploadResult(
                success=True,
                message=f"Diagram '{filename}' imported successfully",
                diagram_id=diagram_id,
                diagram_name=saved_diagram.get('metadata', {}).get('name', filename),
                node_count=len(saved_diagram.get('nodes', {}))
            )
            
        except yaml.YAMLError as e:
            return DiagramUploadResult(
                success=False,
                message=f"Invalid YAML format: {str(e)}"
            )
        except json.JSONDecodeError as e:
            return DiagramUploadResult(
                success=False,
                message=f"Invalid JSON format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Diagram upload error: {str(e)}")
            return DiagramUploadResult(
                success=False,
                message=f"Upload failed: {str(e)}"
            )
    
    @strawberry.mutation
    async def upload_multiple_files(
        self,
        files: List[Upload],
        category: str = "general",
        info: strawberry.Info = None
    ) -> List[FileUploadResult]:
        """
        Upload multiple files at once.
        
        Args:
            files: List of files to upload
            category: Category for organizing uploads
            info: GraphQL context info
            
        Returns:
            List of FileUploadResult for each file
        """
        results = []
        
        for file in files:
            result = await self.upload_file(file, category, info)
            results.append(result)
        
        return results