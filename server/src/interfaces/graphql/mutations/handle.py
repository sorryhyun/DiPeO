"""Refactored handle-related GraphQL mutations using Pydantic models."""
import strawberry
import logging

from ..types.results import HandleResult, DeleteResult
from ..types.scalars import HandleID
from ..types.inputs import CreateHandleInput
from ..context import GraphQLContext
from ....domains.diagram.models.domain import DomainHandle, Vec2
from ..models.input_models import CreateHandleInput as PydanticCreateHandleInput

logger = logging.getLogger(__name__)


@strawberry.type
class HandleMutations:
    """Mutations for handle operations."""
    
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