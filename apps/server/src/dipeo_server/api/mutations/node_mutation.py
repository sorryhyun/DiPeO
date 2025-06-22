"""GraphQL mutations for node operations."""

import logging
import uuid

import strawberry

from dipeo_server.core import NodeType, Vec2
from dipeo_domain import DomainNode

from ..context import GraphQLContext
from ..types.inputs_types import CreateNodeInput, UpdateNodeInput
from ..models.input_models import (
    CreateNodeInput as PydanticCreateNodeInput,
)
from ..models.input_models import (
    UpdateNodeInput as PydanticUpdateNodeInput,
)
from ..types.results_types import DeleteResult, NodeResult
from ..types.scalars_types import DiagramID, NodeID

logger = logging.getLogger(__name__)


@strawberry.type
class NodeMutations:
    """Handles node CRUD operations."""

    @strawberry.mutation
    async def create_node(
        self, diagram_id: DiagramID, input: CreateNodeInput, info
    ) -> NodeResult:
        """Creates new node in diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service

            pydantic_input = PydanticCreateNodeInput(
                type=input.type,
                position={"x": input.position.x, "y": input.position.y},
                label=input.label,
                properties=input.properties or {},
            )

            diagram_data = diagram_service.load_diagram(diagram_id)
            if not diagram_data:
                return NodeResult(success=False, error="Diagram not found")

            node_id = f"node_{str(uuid.uuid4())[:8]}"

            node_properties = pydantic_input.properties.copy()
            node_properties["label"] = pydantic_input.label

            node = DomainNode(
                id=node_id,
                type=pydantic_input.type,
                position=Vec2(x=pydantic_input.position.x, y=pydantic_input.position.y),
                data=node_properties,
            )

            diagram_data["nodes"][node_id] = node.model_dump()

            diagram_service.update_diagram(diagram_id, diagram_data)

            return NodeResult(
                success=True, node=node, message=f"Created node {node_id}"
            )

        except ValueError as e:
            logger.error(f"Validation error creating node: {e}")
            return NodeResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to create node: {e}")
            return NodeResult(success=False, error=f"Failed to create node: {e!s}")

    @strawberry.mutation
    async def update_node(self, input: UpdateNodeInput, info) -> NodeResult:
        """Updates existing node properties."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service

            pydantic_input = PydanticUpdateNodeInput(
                id=input.id,
                position={"x": input.position.x, "y": input.position.y}
                if input.position
                else None,
                label=input.label,
                properties=input.properties,
            )

            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None

            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta["path"])
                if pydantic_input.id in temp_diagram.get("nodes", {}):
                    diagram_id = diagram_meta["path"]
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return NodeResult(
                    success=False,
                    error=f"Node {pydantic_input.id} not found in any diagram",
                )

            node_data = diagram_data["nodes"][pydantic_input.id]

            if pydantic_input.position:
                node_data["position"] = {
                    "x": pydantic_input.position.x,
                    "y": pydantic_input.position.y,
                }

            if pydantic_input.label is not None:
                node_data["data"]["label"] = pydantic_input.label

            if pydantic_input.properties is not None:
                node_data["data"].update(pydantic_input.properties)

            updated_node = DomainNode(
                id=pydantic_input.id,
                type=NodeType(node_data["type"]),
                position=Vec2(
                    x=node_data["position"]["x"], y=node_data["position"]["y"]
                ),
                data=node_data["data"],
            )

            diagram_data["nodes"][pydantic_input.id] = updated_node.model_dump()

            diagram_service.update_diagram(diagram_id, diagram_data)

            return NodeResult(
                success=True,
                node=updated_node,
                message=f"Updated node {pydantic_input.id}",
            )

        except ValueError as e:
            logger.error(f"Validation error updating node: {e}")
            return NodeResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to update node: {e}")
            return NodeResult(success=False, error=f"Failed to update node: {e!s}")

    @strawberry.mutation
    async def delete_node(self, id: NodeID, info) -> DeleteResult:
        """Removes node and connected elements."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_service

            diagrams = diagram_service.list_diagram_files()
            diagram_id = None
            diagram_data = None

            for diagram_meta in diagrams:
                temp_diagram = diagram_service.load_diagram(diagram_meta["path"])
                if id in temp_diagram.get("nodes", {}):
                    diagram_id = diagram_meta["path"]
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return DeleteResult(
                    success=False, error=f"Node {id} not found in any diagram"
                )

            del diagram_data["nodes"][id]

            arrows_to_remove = []
            for arrow_id, arrow in diagram_data.get("arrows", {}).items():
                source_node_id = arrow["source"].split(":")[0]
                target_node_id = arrow["target"].split(":")[0]

                if source_node_id == id or target_node_id == id:
                    arrows_to_remove.append(arrow_id)

            for arrow_id in arrows_to_remove:
                del diagram_data["arrows"][arrow_id]

            handles_to_remove = []
            for handle_id, handle in diagram_data.get("handles", {}).items():
                if handle.get("nodeId") == id:
                    handles_to_remove.append(handle_id)

            for handle_id in handles_to_remove:
                del diagram_data["handles"][handle_id]

            diagram_service.update_diagram(diagram_id, diagram_data)

            return DeleteResult(
                success=True,
                deleted_id=id,
                message=f"Deleted node {id} and {len(arrows_to_remove)} connected arrows",
            )

        except Exception as e:
            logger.error(f"Failed to delete node {id}: {e}")
            return DeleteResult(success=False, error=f"Failed to delete node: {e!s}")
