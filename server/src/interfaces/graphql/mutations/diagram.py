"""Refactored diagram-related GraphQL mutations using Pydantic models."""
import strawberry
from typing import Optional
import logging
from datetime import datetime

from ..types.results import DiagramResult, DeleteResult
from ..types.scalars import DiagramID
from ..types.inputs import CreateDiagramInput, ImportYamlInput
from ..types.enums import DiagramFormat
from ..context import GraphQLContext
from src.domains.diagram.models.domain import DiagramMetadata, DomainDiagram
from ..models.input_models import (
    CreateDiagramInput as PydanticCreateDiagramInput,
    ImportYamlInput as PydanticImportYamlInput
)

logger = logging.getLogger(__name__)


@strawberry.type
class DiagramMutations:
    """Mutations for diagram operations."""
    
    @strawberry.mutation
    async def create_diagram(self, input: CreateDiagramInput, info) -> DiagramResult:
        """Create a new diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticCreateDiagramInput(
                name=input.name,
                description=input.description,
                author=input.author,
                tags=input.tags
            )
            
            # Create diagram metadata using validated Pydantic data
            metadata = DiagramMetadata(
                name=pydantic_input.name,  # Already trimmed by validation
                description=pydantic_input.description or "",
                author=pydantic_input.author or "",
                tags=pydantic_input.tags,  # Already cleaned of duplicates
                created=datetime.now(),
                modified=datetime.now()
            )
            
            # Create empty diagram structure using Pydantic model
            diagram_model = DomainDiagram(
                nodes={},
                arrows={},
                handles={},
                persons={},
                api_keys={},
                metadata=metadata
            )
            
            # Convert to dict for service
            diagram_data = diagram_model.model_dump()
            
            # Create the diagram file
            path = diagram_service.create_diagram(pydantic_input.name, diagram_data)
            
            # Convert to GraphQL format
            graphql_diagram = diagram_model.to_graphql()
            
            return DiagramResult(
                success=True,
                diagram=graphql_diagram,
                message=f"Created diagram at {path}"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error creating diagram: {e}")
            return DiagramResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create diagram: {e}")
            return DiagramResult(
                success=False,
                error=f"Failed to create diagram: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_diagram(self, id: DiagramID, info) -> DeleteResult:
        """Delete a diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # DiagramID is the path to the diagram file
            diagram_service.delete_diagram(id)
            
            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted diagram: {id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete diagram {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete diagram: {str(e)}"
            )
    
    @strawberry.mutation
    async def save_diagram(self, info, diagram_id: DiagramID, format: Optional[DiagramFormat] = None) -> DiagramResult:
        """Save diagram to file system (replaces REST endpoint)."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Get the diagram using the diagram_id
            diagram_data = await diagram_service.get_diagram(diagram_id)
            if not diagram_data:
                return DiagramResult(
                    success=False,
                    error=f"Diagram {diagram_id} not found"
                )
            
            # Determine filename and format
            format_str = format.value if format else "native"
            
            # Map format to directory and extension
            format_mapping = {
                "native": ("", ".json"),
                "light": ("light", ".light.yaml"),
                "readable": ("readable", ".readable.yaml"),
                "llm": ("llm", ".llm.yaml")
            }
            
            directory, extension = format_mapping.get(format_str, ("", ".json"))
            
            # Generate filename with proper path
            if directory:
                filename = f"{directory}/{diagram_id}{extension}"
            else:
                filename = f"{diagram_id}{extension}"
            
            # Use the converter system to export in the desired format
            from src.domains.diagram.converters.registry import converter_registry
            converter = converter_registry.get(format_str)
            
            if not converter:
                return DiagramResult(
                    success=False,
                    error=f"Unknown format: {format_str}"
                )
            
            # Convert to the desired format
            domain_diagram = DomainDiagram.from_dict(diagram_data)
            content = converter.serialize(domain_diagram)
            
            # Save to file
            file_path = diagram_service.diagrams_dir / filename
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            path = str(filename)
            
            # Convert to GraphQL type using built-in method
            domain_diagram = DomainDiagram.from_dict(diagram_data)
            graphql_diagram = domain_diagram.to_graphql()
            
            return DiagramResult(
                success=True,
                diagram=graphql_diagram,
                message=f"Diagram saved to {path}"
            )
            
        except Exception as e:
            logger.error(f"Failed to save diagram: {e}")
            return DiagramResult(
                success=False,
                error=f"Failed to save diagram: {str(e)}"
            )
    
    @strawberry.mutation
    async def convert_diagram(self, info, diagram_id: DiagramID, target_format: DiagramFormat) -> DiagramResult:
        """Convert diagram between formats (JSON, YAML, LLM-YAML)."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Get the diagram using the diagram_id
            diagram_data = await diagram_service.get_diagram(diagram_id)
            if not diagram_data:
                return DiagramResult(
                    success=False,
                    error=f"Diagram {diagram_id} not found"
                )
            
            # Format validation is now handled by the enum type
            
            # Save in new format
            # Create new filename with target extension
            import os
            base_name = os.path.splitext(diagram_id)[0]
            
            # Map format to file extension
            extension_map = {
                DiagramFormat.NATIVE: '.json',
                DiagramFormat.LIGHT: '.yaml',
                DiagramFormat.READABLE: '.yaml', 
                DiagramFormat.LLM: '.yaml'
            }
            extension = extension_map.get(target_format, '.yaml')
            new_diagram_id = f"{base_name}{extension}"
            
            # Save diagram in new format
            path = diagram_service.save_diagram(new_diagram_id, diagram_data, target_format.value)
            
            # Load and return the converted diagram
            converted_data = diagram_service.load_diagram(new_diagram_id)
            domain_diagram = DomainDiagram.from_dict(converted_data)
            graphql_diagram = domain_diagram.to_graphql()
            
            return DiagramResult(
                success=True,
                diagram=graphql_diagram,
                message=f"Diagram converted to {target_format.value} and saved to {path}"
            )
            
        except Exception as e:
            logger.error(f"Failed to convert diagram: {e}")
            return DiagramResult(
                success=False,
                error=f"Failed to convert diagram: {str(e)}"
            )
    
    @strawberry.mutation
    async def import_yaml_diagram(self, input: ImportYamlInput, info) -> DiagramResult:
        """Import a YAML diagram (replaces REST endpoint)."""
        try:
            import yaml
            from pathlib import Path
            
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticImportYamlInput(
                content=input.content,
                filename=input.filename
            )
            
            # Parse YAML content - validated content is guaranteed non-empty
            try:
                diagram_data = yaml.safe_load(pydantic_input.content)
            except yaml.YAMLError as e:
                return DiagramResult(
                    success=False,
                    error=f"Invalid YAML format: {str(e)}"
                )
            
            # Validate it's a diagram
            if not isinstance(diagram_data, dict):
                return DiagramResult(
                    success=False,
                    error="YAML content must be a dictionary representing a diagram"
                )
            
            # Generate filename if not provided
            if pydantic_input.filename:
                # Validated filename is guaranteed clean
                filename = pydantic_input.filename
                if not filename.endswith(('.yaml', '.yml')):
                    filename += '.yaml'
            else:
                # Generate filename from diagram name or timestamp
                diagram_name = diagram_data.get('metadata', {}).get('name', 'imported')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{diagram_name}_{timestamp}.yaml"
            
            # Save the diagram
            path = diagram_service.save_diagram(filename, diagram_data, 'yaml')
            
            # Load and convert to GraphQL type using built-in method
            loaded_diagram = diagram_service.load_diagram(filename)
            domain_diagram = DomainDiagram.from_dict(loaded_diagram)
            graphql_diagram = domain_diagram.to_graphql()
            
            return DiagramResult(
                success=True,
                diagram=graphql_diagram,
                message=f"YAML diagram imported successfully as {filename}"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error importing YAML: {e}")
            return DiagramResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to import YAML diagram: {e}")
            return DiagramResult(
                success=False,
                error=f"Failed to import YAML diagram: {str(e)}"
            )