"""GraphQL mutations for diagram arrows and handles."""

import logging
import uuid

import strawberry

from dipeo_server.core import Vec2
from dipeo_server.domains.diagram.converters import diagram_dict_to_graphql
from dipeo_domain import (
    DiagramDictFormat,
    DomainArrow,
    DomainHandle,
)

from ..context import GraphQLContext
from ..types.inputs_types import CreateArrowInput, CreateHandleInput
from ..models.input_models import (
    CreateArrowInput as PydanticCreateArrowInput,
)
from ..models.input_models import (
    CreateHandleInput as PydanticCreateHandleInput,
)
from ..types.results_types import DeleteResult, DiagramResult, HandleResult
from ..types.scalars_types import ArrowID, DiagramID, HandleID

logger = logging.getLogger(__name__)


@strawberry.type
class GraphElementMutations:
    """Handles arrow and handle CRUD operations."""

    @strawberry.mutation
    async def create_arrow(
        self, diagram_id: DiagramID, input: CreateArrowInput, info
    ) -> DiagramResult:
        """Creates arrow connection between handles."""
        try:
            context: GraphQLContext = info.context
            storage_service = context.diagram_storage_service
            converter_service = context.diagram_converter_service

            pydantic_input = PydanticCreateArrowInput(
                source=input.source, target=input.target, label=input.label
            )

            # Load diagram using new services
            path = await storage_service.find_by_id(diagram_id)
            if not path:
                return DiagramResult(success=False, error="Diagram not found")
            
            diagram_data = await storage_service.read_file(path)

            source_node_id, source_handle = pydantic_input.source.split(":")
            target_node_id, target_handle = pydantic_input.target.split(":")

            if source_node_id not in diagram_data.get("nodes", {}):
                return DiagramResult(
                    success=False, error=f"Source node {source_node_id} not found"
                )

            if target_node_id not in diagram_data.get("nodes", {}):
                return DiagramResult(
                    success=False, error=f"Target node {target_node_id} not found"
                )

            arrow_id = f"arrow_{str(uuid.uuid4())[:8]}"

            arrow = DomainArrow(
                id=arrow_id,
                source=pydantic_input.source,
                target=pydantic_input.target,
                data={"label": pydantic_input.label} if pydantic_input.label else None,
            )

            if "arrows" not in diagram_data:
                diagram_data["arrows"] = {}
            diagram_data["arrows"][arrow_id] = arrow.model_dump()

            # Save diagram using new service
            await storage_service.write_file(path, diagram_data)

            diagram_dict_format = DiagramDictFormat.model_validate(diagram_data)
            graphql_diagram = diagram_dict_to_graphql(diagram_dict_format)

            return DiagramResult(
                success=True,
                diagram=graphql_diagram,
                message=f"Created arrow {arrow_id}",
            )

        except ValueError as e:
            logger.error(f"Validation error creating arrow: {e}")
            return DiagramResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to create arrow: {e}")
            return DiagramResult(
                success=False, error=f"Failed to create arrow: {e!s}"
            )

    @strawberry.mutation
    async def delete_arrow(self, id: ArrowID, info) -> DeleteResult:
        """Removes arrow from diagram."""
        try:
            context: GraphQLContext = info.context
            storage_service = context.diagram_storage_service

            # Search for the arrow in all diagrams
            file_infos = await storage_service.list_files()
            diagram_path = None
            diagram_data = None

            for file_info in file_infos:
                temp_diagram = await storage_service.read_file(file_info.path)
                if id in temp_diagram.get("arrows", {}):
                    diagram_path = file_info.path
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return DeleteResult(
                    success=False, error=f"Arrow {id} not found in any diagram"
                )

            del diagram_data["arrows"][id]

            # Save diagram using new service
            await storage_service.write_file(diagram_path, diagram_data)

            return DeleteResult(
                success=True, deleted_id=id, message=f"Deleted arrow {id}"
            )

        except Exception as e:
            logger.error(f"Failed to delete arrow {id}: {e}")
            return DeleteResult(
                success=False, error=f"Failed to delete arrow: {e!s}"
            )

    @strawberry.mutation
    async def create_handle(self, input: CreateHandleInput, info) -> HandleResult:
        """Creates handle for node connection point."""
        try:
            context: GraphQLContext = info.context
            storage_service = context.diagram_storage_service

            pydantic_input = PydanticCreateHandleInput(
                node_id=input.node_id,
                label=input.label,
                direction=input.direction,
                data_type=input.data_type,
                position={"x": input.position.x, "y": input.position.y}
                if input.position
                else None,
                max_connections=input.max_connections,
            )

            # Find diagram containing this node
            file_infos = await storage_service.list_files()
            diagram_path = None
            diagram_data = None

            for file_info in file_infos:
                temp_diagram = await storage_service.read_file(file_info.path)
                if pydantic_input.node_id in temp_diagram.get("nodes", {}):
                    diagram_path = file_info.path
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return HandleResult(
                    success=False,
                    error=f"Node {pydantic_input.node_id} not found in any diagram",
                )

            handle_id = f"{pydantic_input.node_id}:{pydantic_input.label}"

            if handle_id in diagram_data.get("handles", {}):
                return HandleResult(
                    success=False,
                    error=f"Handle '{pydantic_input.label}' already exists for node {pydantic_input.node_id}",
                )

            handle = DomainHandle(
                id=handle_id,
                nodeId=pydantic_input.node_id,
                label=pydantic_input.label,
                direction=pydantic_input.direction,
                dataType=pydantic_input.data_type,
                maxConnections=pydantic_input.max_connections,
                position=Vec2(
                    x=pydantic_input.position["x"], y=pydantic_input.position["y"]
                )
                if pydantic_input.position
                else None,
            )

            if "handles" not in diagram_data:
                diagram_data["handles"] = {}
            diagram_data["handles"][handle_id] = handle.model_dump()

            # Save diagram using new service
            await storage_service.write_file(path, diagram_data)

            return HandleResult(
                success=True, handle=handle, message=f"Created handle {handle_id}"
            )

        except ValueError as e:
            # Pydantic validation error
            logger.error(f"Validation error creating handle: {e}")
            return HandleResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to create handle: {e}")
            return HandleResult(
                success=False, error=f"Failed to create handle: {e!s}"
            )

    @strawberry.mutation
    async def delete_handle(self, id: HandleID, info) -> DeleteResult:
        """Removes handle and connected arrows."""
        try:
            context: GraphQLContext = info.context
            storage_service = context.diagram_storage_service

            # Find diagram containing this handle
            file_infos = await storage_service.list_files()
            diagram_path = None
            diagram_data = None

            for file_info in file_infos:
                temp_diagram = await storage_service.read_file(file_info.path)
                if id in temp_diagram.get("handles", {}):
                    diagram_path = file_info.path
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return DeleteResult(
                    success=False, error=f"Handle {id} not found in any diagram"
                )

            del diagram_data["handles"][id]

            arrows_to_remove = []
            for arrow_id, arrow in diagram_data.get("arrows", {}).items():
                if arrow["source"] == id or arrow["target"] == id:
                    arrows_to_remove.append(arrow_id)

            for arrow_id in arrows_to_remove:
                del diagram_data["arrows"][arrow_id]

            # Save diagram using new service
            await storage_service.write_file(diagram_path, diagram_data)

            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted handle {id} and {len(arrows_to_remove)} connected arrows",
            )

        except Exception as e:
            logger.error(f"Failed to delete handle {id}: {e}")
            return DeleteResult(
                success=False, error=f"Failed to delete handle: {e!s}"
            )
