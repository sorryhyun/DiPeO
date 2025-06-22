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

from dipeo_server.domains.diagram import DiagramService
from dipeo_server.core.services import APIKeyService
from dipeo_server.domains.diagram.models import DiagramMetadata, DomainDiagram, DiagramDictFormat
from dipeo_server.domains.diagram.converters import converter_registry, diagram_dict_to_graphql
from .context import GraphQLContext
from .results_types import FileUploadResult
from .scalars_types import DiagramID, JSONScalar
from .enums_types import DiagramFormat

logger = logging.getLogger(__name__)

def validate_diagram(diagram: DomainDiagram, api_key_service: Optional[APIKeyService] = None) -> List[str]:
    """Validate diagram structure and return errors."""
    errors = []
    
    # Check for at least one node
    if not diagram.nodes:
        errors.append("Diagram must have at least one node")
    
    # Validate node references in arrows
    # DomainDiagram has lists, not dicts
    node_ids = set(node.id for node in diagram.nodes)
    handle_ids = set(handle.id for handle in diagram.handles)
    
    for arrow in diagram.arrows:
        # Check if source handle exists
        if arrow.source not in handle_ids:
            # Check if it's a node reference that needs handle
            source_node_id = arrow.source.split(':')[0]
            if source_node_id not in node_ids:
                errors.append(f"Arrow {arrow.id} references unknown source: {arrow.source}")
        
        # Check if target handle exists
        if arrow.target not in handle_ids:
            target_node_id = arrow.target.split(':')[0]
            if target_node_id not in node_ids:
                errors.append(f"Arrow {arrow.id} references unknown target: {arrow.target}")
    
    # Validate handle node references
    for handle in diagram.handles:
        if handle.node_id not in node_ids:
            errors.append(f"Handle {handle.id} references unknown node: {handle.node_id}")
    
    # Validate person assignments
    person_ids = set(person.id for person in diagram.persons)
    for node in diagram.nodes:
        person_id = node.data.get('personId') if node.data else None
        if person_id and person_id not in person_ids:
            errors.append(f"Node {node.id} references unknown person: {person_id}")
    
    # Validate person API key references against external API key store
    if api_key_service:
        # Get all available API keys from the service
        api_key_ids = set(api_key_service._store.keys())
        for person in diagram.persons:
            if person.api_key_id and person.api_key_id not in api_key_ids:
                errors.append(f"Person {person.id} references unknown API key: {person.api_key_id}")
    else:
        # Fallback to checking embedded keys if no service provided
        api_key_ids = set(api_key.id for api_key in diagram.api_keys)
        for person in diagram.persons:
            if person.api_key_id and person.api_key_id not in api_key_ids:
                errors.append(f"Person {person.id} references unknown API key: {person.api_key_id}")
    
    return errors

def domain_to_storage_format(diagram: DomainDiagram) -> Dict[str, Any]:
    """Convert domain diagram to storage format (dict)."""
    # Use native converter for storage
    converter = converter_registry.get(DiagramFormat.native.value)
    json_str = converter.serialize(diagram)
    data = json.loads(json_str)
    
    # Ensure all collections are in dict format, not lists
    if isinstance(data.get('nodes'), list):
        data['nodes'] = {node['id']: node for node in data['nodes']}
    if isinstance(data.get('arrows'), list):
        data['arrows'] = {arrow['id']: arrow for arrow in data['arrows']}
    if isinstance(data.get('handles'), list):
        data['handles'] = {handle['id']: handle for handle in data['handles']}
    if isinstance(data.get('persons'), list):
        data['persons'] = {person['id']: person for person in data['persons']}
    if isinstance(data.get('api_keys'), list):
        data['api_keys'] = {api_key['id']: api_key for api_key in data['api_keys']}
    
    return data

def storage_to_domain_format(data: Dict[str, Any]) -> DomainDiagram:
    """Convert storage format to domain diagram."""
    # Convert dict to string then parse with native converter
    converter = converter_registry.get(DiagramFormat.native.value)
    # Native format is now JSON, so use JSON serialization
    json_str = json.dumps(data, indent=2)
    return converter.deserialize(json_str)

@strawberry.type
class DiagramSaveResult:
    """Result of a diagram file save."""
    success: bool
    message: str
    diagram_id: Optional[DiagramID] = None
    diagram_name: Optional[str] = None
    node_count: Optional[int] = None
    format_detected: Optional[str] = None

@strawberry.type  
class DiagramConvertResult:
    """Result of diagram conversion operation."""
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
                path=str(file_path),
                size_bytes=file_size,
                content_type=file_type
            )
            
        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            return FileUploadResult(
                success=False,
                message=f"Upload failed: {str(e)}",
                error=str(e)
            )
    
    @strawberry.mutation
    async def save_diagram(
        self,
        file: Upload,
        format: Optional[str] = None,
        validate_only: bool = False,
        info: strawberry.Info = None
    ) -> DiagramSaveResult:
        context: GraphQLContext = info.context
        
        try:
            # Read file content
            content = await file.read()
            content_str = content.decode('utf-8')
            filename = file.filename or "unnamed_diagram"
            
            # Validate file size (5MB limit for diagrams)
            if len(content) > 5 * 1024 * 1024:
                return DiagramSaveResult(
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
                        detected_format = DiagramFormat.light.value
                    elif 'readable' in filename:
                        detected_format = DiagramFormat.readable.value
                    elif 'native.yaml' in filename or 'native_yaml' in filename:
                        detected_format = DiagramFormat.native_yaml.value
                    else:
                        detected_format = DiagramFormat.native.value  # Default
            
            # Get converter
            converter = converter_registry.get(detected_format)
            if not converter:
                return DiagramSaveResult(
                    success=False,
                    message=f"Unknown format: {detected_format}"
                )
            
            # Check if format supports import
            format_info = converter_registry.get_info(detected_format)
            if not format_info.get('supports_import', True):
                return DiagramSaveResult(
                    success=False,
                    message=f"Format '{detected_format}' does not support import"
                )
            
            # Parse diagram
            try:
                domain_diagram = converter.deserialize(content_str)
            except Exception as e:
                return DiagramSaveResult(
                    success=False,
                    message=f"Failed to parse {detected_format} format: {str(e)}"
                )
            
            # Validate diagram structure
            validation_errors = validate_diagram(domain_diagram, context.api_key_service)
            if validation_errors:
                return DiagramSaveResult(
                    success=False,
                    message=f"Validation failed: {'; '.join(validation_errors)}"
                )
            
            if validate_only:
                return DiagramSaveResult(
                    success=True,
                    message="Diagram is valid",
                    node_count=len(domain_diagram.nodes),
                    format_detected=detected_format
                )
            
            # Convert to storage format (native dict)
            storage_data = domain_to_storage_format(domain_diagram)
            
            # Save via diagram service
            diagram_id = await context.diagram_service.save_diagram_with_id(storage_data, filename)
            
            logger.info(f"Diagram saved: {filename} -> {diagram_id} (format: {detected_format})")
            
            return DiagramSaveResult(
                success=True,
                message=f"Successfully saved {filename}",
                diagram_id=diagram_id,
                diagram_name=storage_data.get('metadata', {}).get('name', filename),
                node_count=len(domain_diagram.nodes),
                format_detected=detected_format
            )
            
        except Exception as e:
            logger.error(f"Diagram save error: {str(e)}")
            return DiagramSaveResult(
                success=False,
                message=f"Save failed: {str(e)}"
            )
    
    @strawberry.mutation
    async def convert_diagram(
        self,
        content: JSONScalar,
        format: DiagramFormat = DiagramFormat.native,
        include_metadata: bool = True,
        info: strawberry.Info = None
    ) -> DiagramConvertResult:
        context: GraphQLContext = info.context
        
        try:
            # Validate content is a dict
            if not isinstance(content, dict):
                return DiagramConvertResult(
                    success=False,
                    error="Content must be a JSON object representing a diagram"
                )
            
            # Get converter
            converter = converter_registry.get(format.value)
            if not converter:
                return DiagramConvertResult(
                    success=False,
                    error=f"Unknown format: {format.value}"
                )
            
            # Check if format supports export
            format_info = converter_registry.get_info(format.value)
            if not format_info.get('supports_export', True):
                return DiagramConvertResult(
                    success=False,
                    error=f"Format '{format.value}' does not support export"
                )
            
            # Convert content to domain model
            try:
                diagram_dict_format = DiagramDictFormat.model_validate(content)
                domain_diagram = diagram_dict_to_graphql(diagram_dict_format)
            except Exception as e:
                return DiagramConvertResult(
                    success=False,
                    error=f"Invalid diagram structure: {str(e)}"
                )
            
            # Remove metadata if requested
            if not include_metadata:
                domain_diagram.metadata = DiagramMetadata(version="2.0.0")
            
            # Serialize to requested format
            content_str = converter.serialize(domain_diagram)
            
            # Generate filename
            diagram_name = content.get('metadata', {}).get('name', 'diagram')
            extension = format_info.get('extension', '.yaml')
            filename = f"{diagram_name}{extension}"
            
            return DiagramConvertResult(
                success=True,
                message=f"Exported as {format.value} format",
                content=content_str,
                format=format.value,
                filename=filename
            )
            
        except Exception as e:
            logger.error(f"Stateful export error: {str(e)}", exc_info=True)
            return DiagramConvertResult(
                success=False,
                error=str(e)
            )
