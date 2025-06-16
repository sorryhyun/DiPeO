"""
GraphQL mutations for diagram file upload and export operations.
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
from ...domain import DomainDiagram, DiagramMetadata
from ...converters import converter_registry
from ..context import GraphQLContext
from ..types.results import OperationError
from ..types.scalars import DiagramID
from ..types.enums import DiagramFormat

logger = logging.getLogger(__name__)


@strawberry.type
class DiagramUploadResult:
    """Result of diagram upload operation."""
    success: bool
    message: str
    error: Optional[str] = None
    diagram_id: Optional[DiagramID] = None
    diagram_name: Optional[str] = None
    node_count: Optional[int] = None
    format_detected: Optional[str] = None


@strawberry.type
class DiagramExportResult:
    """Result of diagram export operation."""
    success: bool
    message: str
    error: Optional[str] = None
    content: Optional[str] = None
    format: Optional[str] = None
    filename: Optional[str] = None


@strawberry.type
class DiagramFormatInfo:
    """Information about a diagram format."""
    id: str
    name: str
    description: str
    extension: str
    supports_import: bool
    supports_export: bool


@strawberry.type
class DiagramFileMutations:
    """Mutations for diagram file operations."""
    
    @strawberry.mutation
    async def upload_diagram(
        self,
        info: strawberry.Info[GraphQLContext],
        file: Upload,
        format: Optional[str] = None,
        validate_only: bool = False
    ) -> DiagramUploadResult:
        """
        Upload a diagram file (YAML/JSON) and convert to executable format.
        
        Args:
            file: The uploaded file
            format: Optional format hint (native, light, readable, llm)
            validate_only: If true, only validate without saving
        """
        try:
            # Read file content
            content = await file.read()
            content_str = content.decode('utf-8')
            filename = file.filename or "unnamed_diagram"
            
            # Detect format if not provided
            detected_format = format
            if not detected_format:
                detected_format = converter_registry.detect_format(content_str)
                if not detected_format:
                    # Try to detect from file extension
                    ext = Path(filename).suffix.lower()
                    if ext == '.json':
                        detected_format = 'json'
                    else:
                        detected_format = DiagramFormat.NATIVE.value  # Default
            
            # Get converter
            converter = converter_registry.get(detected_format)
            if not converter:
                return DiagramUploadResult(
                    success=False,
                    message=f"Unsupported format: {detected_format}",
                    error="Format not supported"
                )
            
            # Check if format supports import
            format_info = converter_registry.get_info(detected_format)
            if not format_info.get('supports_import', True):
                return DiagramUploadResult(
                    success=False,
                    message=f"Format '{detected_format}' is export-only",
                    error="Import not supported for this format"
                )
            
            # Parse diagram
            try:
                if detected_format == 'json':
                    # Handle JSON separately
                    data = json.loads(content_str)
                    domain_diagram = DomainDiagram(**data)
                else:
                    domain_diagram = converter.deserialize(content_str)
            except Exception as e:
                return DiagramUploadResult(
                    success=False,
                    message="Failed to parse diagram",
                    error=str(e)
                )
            
            # Validate diagram structure
            validation_errors = self._validate_diagram(domain_diagram)
            if validation_errors:
                return DiagramUploadResult(
                    success=False,
                    message="Diagram validation failed",
                    error="; ".join(validation_errors)
                )
            
            if validate_only:
                return DiagramUploadResult(
                    success=True,
                    message="Diagram is valid",
                    node_count=len(domain_diagram.nodes),
                    format_detected=detected_format
                )
            
            # Generate diagram ID
            diagram_id = str(uuid.uuid4())
            
            # Set metadata if not present
            if not domain_diagram.metadata:
                domain_diagram.metadata = DiagramMetadata()
            
            if not domain_diagram.metadata.name:
                domain_diagram.metadata.name = Path(filename).stem
            
            domain_diagram.metadata.id = diagram_id
            
            # Save to database/storage via service
            diagram_service: DiagramService = info.context.diagram_service
            
            # Convert to dict for storage
            diagram_dict = domain_diagram.model_dump()
            saved_id = await diagram_service.save_diagram_with_id(diagram_dict, filename)
            
            logger.info(f"Diagram uploaded: {filename} -> {saved_id} (format: {detected_format})")
            
            return DiagramUploadResult(
                success=True,
                message=f"Successfully uploaded {filename}",
                diagram_id=saved_id,
                diagram_name=domain_diagram.metadata.name,
                node_count=len(domain_diagram.nodes),
                format_detected=detected_format
            )
            
        except Exception as e:
            logger.error(f"Diagram upload error: {str(e)}")
            return DiagramUploadResult(
                success=False,
                message="Upload failed",
                error=str(e)
            )
    
    @strawberry.mutation
    async def export_diagram(
        self,
        info: strawberry.Info[GraphQLContext],
        diagram_id: DiagramID,
        format: DiagramFormat = DiagramFormat.NATIVE,
        include_metadata: bool = True
    ) -> DiagramExportResult:
        """
        Export a diagram to specified format.
        
        Args:
            diagram_id: ID of the diagram to export
            format: Export format (native, light, readable, llm)
            include_metadata: Whether to include metadata in export
        """
        try:
            # Get converter
            converter = converter_registry.get(format.value)
            if not converter:
                return DiagramExportResult(
                    success=False,
                    message=f"Unknown format: {format.value}",
                    error="Format not supported"
                )
            
            # Check if format supports export
            format_info = converter_registry.get_info(format.value)
            if not format_info.get('supports_export', True):
                return DiagramExportResult(
                    success=False,
                    message=f"Format '{format.value}' does not support export",
                    error="Export not supported for this format"
                )
            
            # Fetch diagram via service
            diagram_service: DiagramService = info.context.diagram_service
            diagram_dict = await diagram_service.get_diagram(diagram_id)
            
            if not diagram_dict:
                return DiagramExportResult(
                    success=False,
                    message="Diagram not found",
                    error=f"No diagram with ID: {diagram_id}"
                )
            
            # Convert to domain model
            domain_diagram = DomainDiagram(**diagram_dict)
            
            # Remove metadata if requested
            if not include_metadata:
                domain_diagram.metadata = None
            
            # Serialize to format
            content = converter.serialize(domain_diagram)
            
            # Generate filename
            diagram_name = (domain_diagram.metadata.name 
                          if domain_diagram.metadata and domain_diagram.metadata.name 
                          else "diagram")
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
            logger.error(f"Diagram export error: {str(e)}")
            return DiagramExportResult(
                success=False,
                message="Export failed",
                error=str(e)
            )
    
    # Note: list_diagram_formats mutation has been removed.
    # Use the 'supportedFormats' query instead.
    
    def _validate_diagram(self, diagram: DomainDiagram) -> List[str]:
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
                # Check if it's a node:handle format
                source_parts = arrow.source.split(':')
                if len(source_parts) == 2:
                    source_node_id = source_parts[0]
                    if source_node_id not in node_ids:
                        errors.append(f"Arrow {arrow_id} references unknown source node: {source_node_id}")
                else:
                    errors.append(f"Arrow {arrow_id} has invalid source format: {arrow.source}")
            
            # Check if target handle exists
            if arrow.target not in handle_ids:
                # Check if it's a node:handle format
                target_parts = arrow.target.split(':')
                if len(target_parts) == 2:
                    target_node_id = target_parts[0]
                    if target_node_id not in node_ids:
                        errors.append(f"Arrow {arrow_id} references unknown target node: {target_node_id}")
                else:
                    errors.append(f"Arrow {arrow_id} has invalid target format: {arrow.target}")
        
        # Validate handle node references
        for handle_id, handle in diagram.handles.items():
            if handle.nodeId not in node_ids:
                errors.append(f"Handle {handle_id} references unknown node: {handle.nodeId}")
        
        # Validate person references in nodes
        person_ids = set(diagram.persons.keys())
        for node_id, node in diagram.nodes.items():
            if 'personId' in node.data and node.data['personId']:
                if node.data['personId'] not in person_ids:
                    errors.append(f"Node {node_id} references unknown person: {node.data['personId']}")
        
        # Validate API key references in persons
        api_key_ids = set(diagram.api_keys.keys())
        for person_id, person in diagram.persons.items():
            if person.apiKeyId and person.apiKeyId not in api_key_ids:
                errors.append(f"Person {person_id} references unknown API key: {person.apiKeyId}")
        
        return errors