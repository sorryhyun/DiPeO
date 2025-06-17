"""Refactored arrow-related GraphQL mutations using Pydantic models."""
import strawberry
import logging
import uuid

from ..types.results import DiagramResult, DeleteResult
from ..types.scalars import DiagramID, ArrowID
from ..types.inputs import CreateArrowInput
from ..context import GraphQLContext
from ....domains.diagram.models.domain import DomainArrow, DomainDiagram
from ..models.input_models import CreateArrowInput as PydanticCreateArrowInput

logger = logging.getLogger(__name__)


@strawberry.type
class ArrowMutations:
    """Mutations for arrow operations."""
    
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
            domain_diagram = DomainDiagram.from_dict(diagram_data)
            graphql_diagram = domain_diagram.to_graphql()
            
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