"""Consolidated mutations for graph elements (arrows and handles) using Pydantic models."""
import strawberry
import logging
import uuid

from .results_types import DiagramResult, HandleResult, DeleteResult
from .scalars_types import DiagramID, ArrowID, HandleID
from .inputs_types import CreateArrowInput, CreateHandleInput
from .context import GraphQLContext
from dipeo_server.domains.diagram.models import DomainArrow, DomainHandle, DomainDiagram, DiagramDictFormat
from dipeo_server.domains.diagram.converters import diagram_dict_to_graphql
from dipeo_server.core import Vec2
from .models.input_models import (
    CreateArrowInput as PydanticCreateArrowInput,
    CreateHandleInput as PydanticCreateHandleInput
)

logger = logging.getLogger(__name__)


@strawberry.type
class GraphElementMutations:
    """Mutations for graph element operations (arrows and handles)."""
    
    # Arrow mutations
    
    @strawberry.mutation
    async def create_arrow(
        self, 
        diagram_id: DiagramID,
        input: CreateArrowInput,
        info
    ) -> DiagramResult:
        """Create a new arrow between handles."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticCreateArrowInput(
                source=input.source,
                target=input.target,
                label=input.label
            )
            
            # Load diagram
            diagram_data = diagram_service.load_diagram(diagram_id)
            if not diagram_data:
                return DiagramResult(
                    success=False,
                    error="Diagram not found"
                )
            
            # Validate that source and target handles exist
            source_node_id, source_handle = pydantic_input.source.split(':')
            target_node_id, target_handle = pydantic_input.target.split(':')
            
            # Check if nodes exist
            if source_node_id not in diagram_data.get('nodes', {}):
                return DiagramResult(
                    success=False,
                    error=f"Source node {source_node_id} not found"
                )
            
            if target_node_id not in diagram_data.get('nodes', {}):
                return DiagramResult(
                    success=False,
                    error=f"Target node {target_node_id} not found"
                )
            
            # Generate arrow ID
            arrow_id = f"arrow_{str(uuid.uuid4())[:8]}"
            
            # Create Pydantic arrow model
            arrow = DomainArrow(
                id=arrow_id,
                source=pydantic_input.source,  # Already validated format
                target=pydantic_input.target,  # Already validated format
                data={"label": pydantic_input.label} if pydantic_input.label else None
            )
            
            # Add arrow to diagram
            if "arrows" not in diagram_data:
                diagram_data["arrows"] = {}
            diagram_data["arrows"][arrow_id] = arrow.model_dump()
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            # Convert entire diagram to GraphQL type for return
            diagram_dict_format = DiagramDictFormat.model_validate(diagram_data)
            graphql_diagram = diagram_dict_to_graphql(diagram_dict_format)
            
            return DiagramResult(
                success=True,
                diagram=graphql_diagram,
                message=f"Created arrow {arrow_id}"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error creating arrow: {e}")
            return DiagramResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create arrow: {e}")
            return DiagramResult(
                success=False,
                error=f"Failed to create arrow: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_arrow(self, id: ArrowID, info) -> DeleteResult:
        """Delete an arrow."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Find diagram containing this arrow
            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None
            
            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta['path'])
                if id in temp_diagram.get('arrows', {}):
                    diagram_id = diagram_meta['path']
                    diagram_data = temp_diagram
                    break
            
            if not diagram_data:
                return DeleteResult(
                    success=False,
                    error=f"Arrow {id} not found in any diagram"
                )
            
            # Remove arrow
            del diagram_data['arrows'][id]
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted arrow {id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete arrow {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete arrow: {str(e)}"
            )
    
    # Handle mutations
    
    @strawberry.mutation
    async def create_handle(
        self,
        input: CreateHandleInput,
        info
    ) -> HandleResult:
        """Create a new handle for a node."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Convert Strawberry input to Pydantic model for validation
            pydantic_input = PydanticCreateHandleInput(
                node_id=input.node_id,
                label=input.label,
                direction=input.direction,
                data_type=input.data_type,
                position={"x": input.position.x, "y": input.position.y} if input.position else None,
                max_connections=input.max_connections
            )
            
            # Find diagram containing this node
            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None
            
            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta['path'])
                if pydantic_input.node_id in temp_diagram.get('nodes', {}):
                    diagram_id = diagram_meta['path']
                    diagram_data = temp_diagram
                    break
            
            if not diagram_data:
                return HandleResult(
                    success=False,
                    error=f"Node {pydantic_input.node_id} not found in any diagram"
                )
            
            # Generate handle ID using node ID and handle label
            handle_id = f"{pydantic_input.node_id}:{pydantic_input.label}"
            
            # Check if handle already exists
            if handle_id in diagram_data.get('handles', {}):
                return HandleResult(
                    success=False,
                    error=f"Handle '{pydantic_input.label}' already exists for node {pydantic_input.node_id}"
                )
            
            # Create Pydantic handle model
            handle = DomainHandle(
                id=handle_id,
                nodeId=pydantic_input.node_id,
                label=pydantic_input.label,  # Already trimmed by validation
                direction=pydantic_input.direction,
                dataType=pydantic_input.data_type,
                maxConnections=pydantic_input.max_connections,
                position=Vec2(
                    x=pydantic_input.position["x"],
                    y=pydantic_input.position["y"]
                ) if pydantic_input.position else None
            )
            
            # Add handle to diagram
            if "handles" not in diagram_data:
                diagram_data["handles"] = {}
            diagram_data["handles"][handle_id] = handle.model_dump()
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            return HandleResult(
                success=True,
                handle=handle,  # Strawberry will handle conversion
                message=f"Created handle {handle_id}"
            )
            
        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error creating handle: {e}")
            return HandleResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create handle: {e}")
            return HandleResult(
                success=False,
                error=f"Failed to create handle: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_handle(self, id: HandleID, info) -> DeleteResult:
        """Delete a handle."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service
            
            # Find diagram containing this handle
            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None
            
            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta['path'])
                if id in temp_diagram.get('handles', {}):
                    diagram_id = diagram_meta['path']
                    diagram_data = temp_diagram
                    break
            
            if not diagram_data:
                return DeleteResult(
                    success=False,
                    error=f"Handle {id} not found in any diagram"
                )
            
            # Remove handle
            del diagram_data['handles'][id]
            
            # Remove any arrows connected to this handle
            arrows_to_remove = []
            for arrow_id, arrow in diagram_data.get('arrows', {}).items():
                if arrow['source'] == id or arrow['target'] == id:
                    arrows_to_remove.append(arrow_id)
            
            for arrow_id in arrows_to_remove:
                del diagram_data['arrows'][arrow_id]
            
            # Save updated diagram
            diagram_service.update_diagram(diagram_id, diagram_data)
            
            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted handle {id} and {len(arrows_to_remove)} connected arrows"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete handle {id}: {e}")
            return DeleteResult(
                success=False,
                error=f"Failed to delete handle: {str(e)}"
            )