"""
GraphQL mutations for file upload support.

Implements the GraphQL multipart request specification:
https://github.com/jaydenseric/graphql-multipart-request-spec
"""

import strawberry
from strawberry.file_uploads import Upload
from typing import Optional, List, Dict, Any
import yaml
import json
from pathlib import Path
import uuid
import logging

from src.domains.diagram.services.diagram_service import DiagramService
from src.shared.services.api_key_service import APIKeyService
from src.domains.diagram.models.domain import DiagramMetadata, DomainDiagram
from src.domains.diagram.converters import converter_registry
from ..context import GraphQLContext
from ..types.results import FileUploadResult
from ..types.scalars import DiagramID
from ..types.enums import DiagramFormat

logger = logging.getLogger(__name__)

def validate_diagram(diagram: DomainDiagram, api_key_service: Optional[APIKeyService] = None) -> List[str]:
    """Validate diagram structure and return errors."""
    errors = []
    
    # Check for at least one node
    if not diagram.nodes:
        errors.append("Diagram must have at least one node")
    
    # Validate node references in arrows
    node_ids = set(diagram.nodes.keys())
    handle_ids = set(diagram.handles.keys())
    
    for arrow_id, arrow in diagram.arrows.items():
        # Check if source handle exists
        if arrow.source not in handle_ids:
            # Check if it's a node reference that needs handle
            source_node_id = arrow.source.split(':')[0]
            if source_node_id not in node_ids:
                errors.append(f"Arrow {arrow_id} references unknown source: {arrow.source}")
        
        # Check if target handle exists
        if arrow.target not in handle_ids:
            target_node_id = arrow.target.split(':')[0]
            if target_node_id not in node_ids:
                errors.append(f"Arrow {arrow_id} references unknown target: {arrow.target}")
    
    # Validate handle node references
    for handle_id, handle in diagram.handles.items():
        if handle.nodeId not in node_ids:
            errors.append(f"Handle {handle_id} references unknown node: {handle.nodeId}")
    
    # Validate person assignments
    person_ids = set(diagram.persons.keys())
    for node_id, node in diagram.nodes.items():
        person_id = node.data.get('personId')
        if person_id and person_id not in person_ids:
            errors.append(f"Node {node_id} references unknown person: {person_id}")
    
    # Validate person API key references against external API key store
    if api_key_service:
        # Get all available API keys from the service
        api_key_ids = set(api_key_service._store.keys())
        for person_id, person in diagram.persons.items():
            if person.api_key_id and person.api_key_id not in api_key_ids:
                errors.append(f"Person {person_id} references unknown API key: {person.api_key_id}")
    else:
        # Fallback to checking embedded keys if no service provided
        api_key_ids = set(diagram.api_keys.keys())
        for person_id, person in diagram.persons.items():
            if person.api_key_id and person.api_key_id not in api_key_ids:
                errors.append(f"Person {person_id} references unknown API key: {person.api_key_id}")
    
    return errors

def domain_to_storage_format(diagram: DomainDiagram) -> Dict[str, Any]:
    """Convert domain diagram to storage format (dict)."""
    # Use native converter for storage
    converter = converter_registry.get(DiagramFormat.NATIVE.value)
    json_str = converter.serialize(diagram)
    return json.loads(json_str)

def storage_to_domain_format(data: Dict[str, Any]) -> DomainDiagram:
    """Convert storage format to domain diagram."""
    # Convert dict to string then parse with native converter
    converter = converter_registry.get(DiagramFormat.NATIVE.value)
    # Native format is now JSON, so use JSON serialization
    json_str = json.dumps(data, indent=2)
    return converter.deserialize(json_str)

@strawberry.type
class DiagramUploadResult:
    """Result of a diagram file upload."""
    success: bool
    message: str
    diagram_id: Optional[DiagramID] = None
    diagram_name: Optional[str] = None
    node_count: Optional[int] = None
    format_detected: Optional[str] = None

@strawberry.type  
class DiagramExportResult:
    """Result of diagram export operation."""
    success: bool
    message: str = ""
    error: Optional[str] = None
    content: Optional[str] = None
    format: Optional[str] = None
    filename: Optional[str] = None

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
        format: Optional[str] = None,
        validate_only: bool = False,
        info: strawberry.Info = None
    ) -> DiagramUploadResult:
        """
        Upload a diagram file (YAML/JSON) and convert to executable format.
        
        Args:
            file: The uploaded file
            format: Optional format hint (native, light, readable, llm)
            validate_only: If true, only validate without saving
            info: GraphQL context info
            
        Returns:
            DiagramUploadResult with diagram details
        """
        context: GraphQLContext = info.context
        
        try:
            # Read file content
            content = await file.read()
            content_str = content.decode('utf-8')
            filename = file.filename or "unnamed_diagram"
            
            # Validate file size (5MB limit for diagrams)
            if len(content) > 5 * 1024 * 1024:
                return DiagramUploadResult(
                    success=False,
                    message="Diagram file exceeds 5MB limit"
                )
            
            # Detect or validate format
            detected_format = format.lower() if format else None
            if not detected_format:
                detected_format = converter_registry.detect_format(content_str)
                if not detected_format:
                    # Try to infer from extension
                    ext = Path(filename).suffix.lower()
                    if 'light' in filename:
                        detected_format = DiagramFormat.LIGHT.value
                    elif 'readable' in filename:
                        detected_format = DiagramFormat.READABLE.value
                    elif 'llm' in filename:
                        detected_format = DiagramFormat.LLM.value
                    else:
                        detected_format = DiagramFormat.NATIVE.value  # Default
            
            # Get converter
            converter = converter_registry.get(detected_format)
            if not converter:
                return DiagramUploadResult(
                    success=False,
                    message=f"Unknown format: {detected_format}"
                )
            
            # Check if format supports import
            format_info = converter_registry.get_info(detected_format)
            if not format_info.get('supports_import', True):
                return DiagramUploadResult(
                    success=False,
                    message=f"Format '{detected_format}' does not support import"
                )
            
            # Parse diagram
            try:
                domain_diagram = converter.deserialize(content_str)
            except Exception as e:
                return DiagramUploadResult(
                    success=False,
                    message=f"Failed to parse {detected_format} format: {str(e)}"
                )
            
            # Validate diagram structure
            validation_errors = validate_diagram(domain_diagram, context.api_key_service)
            if validation_errors:
                return DiagramUploadResult(
                    success=False,
                    message=f"Validation failed: {'; '.join(validation_errors)}"
                )
            
            if validate_only:
                return DiagramUploadResult(
                    success=True,
                    message="Diagram is valid",
                    node_count=len(domain_diagram.nodes),
                    format_detected=detected_format
                )
            
            # Convert to storage format (native dict)
            storage_data = domain_to_storage_format(domain_diagram)
            
            # Save via diagram service
            diagram_id = await context.diagram_service.save_diagram_with_id(storage_data, filename)
            
            logger.info(f"Diagram uploaded: {filename} -> {diagram_id} (format: {detected_format})")
            
            return DiagramUploadResult(
                success=True,
                message=f"Successfully uploaded {filename}",
                diagram_id=diagram_id,
                diagram_name=storage_data.get('metadata', {}).get('name', filename),
                node_count=len(domain_diagram.nodes),
                format_detected=detected_format
            )
            
        except Exception as e:
            logger.error(f"Diagram upload error: {str(e)}")
            return DiagramUploadResult(
                success=False,
                message=f"Upload failed: {str(e)}"
            )
    
    @strawberry.mutation
    async def export_diagram(
        self,
        diagram_id: DiagramID,
        format: DiagramFormat = DiagramFormat.NATIVE,
        include_metadata: bool = True,
        info: strawberry.Info = None
    ) -> DiagramExportResult:
        """
        Export a diagram to specified format.
        
        Args:
            diagram_id: ID of the diagram to export
            format: Export format (native, light, readable, llm)
            include_metadata: Whether to include metadata in export
            info: GraphQL context info
        """
        context: GraphQLContext = info.context
        
        try:
            # Get converter
            converter = converter_registry.get(format.value)
            if not converter:
                return DiagramExportResult(
                    success=False,
                    error=f"Unknown format: {format.value}"
                )
            
            # Check if format supports export
            format_info = converter_registry.get_info(format.value)
            if not format_info.get('supports_export', True):
                return DiagramExportResult(
                    success=False,
                    error=f"Format '{format.value}' does not support export"
                )
            
            # Fetch diagram
            diagram_data = await context.diagram_service.get_diagram(diagram_id)
            if not diagram_data:
                return DiagramExportResult(
                    success=False,
                    error="Diagram not found"
                )
            
            # Convert storage format to domain model
            domain_diagram = storage_to_domain_format(diagram_data)
            
            # Remove metadata if requested
            if not include_metadata:
                domain_diagram.metadata = DiagramMetadata(version="2.0.0")
            
            # Serialize to requested format
            content = converter.serialize(domain_diagram)
            
            # Generate filename
            diagram_name = diagram_data.get('metadata', {}).get('name', 'diagram')
            extension = format_info.get('extension', '.yaml')
            filename = f"{diagram_name}{extension}"
            
            return DiagramExportResult(
                success=True,
                message=f"Exported as {format.value} format",
                content=content,
                format=format.value,
                filename=filename
            )
            
        except Exception as e:
            logger.error(f"Export error: {str(e)}", exc_info=True)
            return DiagramExportResult(
                success=False,
                error=str(e)
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