"""GraphQL mutations for node operations."""

import logging
import uuid

import strawberry
from dipeo.models import DomainNode, NodeType, Vec2
from dipeo.models import NodeID as DomainNodeID

from ..context import GraphQLContext
from ..types import (
    CreateNodeInput,
    DeleteResult,
    DiagramID,
    NodeID,
    NodeResult,
    UpdateNodeInput,
)

logger = logging.getLogger(__name__)


@strawberry.type
class NodeMutations:
    """Handles node CRUD operations."""

    @strawberry.mutation
    async def create_node(
        self, diagram_id: DiagramID, input_data: CreateNodeInput, info
    ) -> NodeResult:
        """Creates new node in diagram."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_storage_service

            # Use input_data directly without conversion

            # Find the diagram file path
            if diagram_id == "quicksave":
                path = "quicksave.json"
            else:
                path = await diagram_service.find_by_id(diagram_id)
                if not path:
                    return NodeResult(success=False, error="Diagram not found")

            diagram_data = await diagram_service.read_file(path)
            if not diagram_data:
                return NodeResult(success=False, error="Diagram not found")

            node_id = f"node_{str(uuid.uuid4())[:8]}"

            node_properties = (input_data.properties or {}).copy()
            node_properties["label"] = input_data.label

            node = DomainNode(
                id=DomainNodeID(node_id),
                type=input_data.type,
                position=Vec2(x=input_data.position.x, y=input_data.position.y),
                data=node_properties,
            )

            diagram_data["nodes"][node_id] = node.model_dump()

            await diagram_service.write_file(path, diagram_data)

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
    async def update_node(self, input_data: UpdateNodeInput, info) -> NodeResult:
        """Updates existing node properties."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_storage_service

            # Use input_data directly without conversion

            diagrams = await diagram_service.list_files()
            diagram_id = None
            diagram_data = None

            for diagram_meta in diagrams:
                temp_diagram = await diagram_service.read_file(diagram_meta.path)
                if input_data.id in temp_diagram.get("nodes", {}):
                    diagram_id = diagram_meta.path
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return NodeResult(
                    success=False,
                    error=f"Node {input_data.id} not found in any diagram",
                )

            node_data = diagram_data["nodes"][input_data.id]

            if input_data.position:
                node_data["position"] = {
                    "x": input_data.position.x,
                    "y": input_data.position.y,
                }

            if input_data.label is not None:
                node_data["data"]["label"] = input_data.label

            if input_data.properties is not None:
                node_data["data"].update(input_data.properties)

            updated_node = DomainNode(
                id=input_data.id,
                type=NodeType(node_data["type"]),
                position=Vec2(
                    x=node_data["position"]["x"], y=node_data["position"]["y"]
                ),
                data=node_data["data"],
            )

            diagram_data["nodes"][input_data.id] = updated_node.model_dump()

            await diagram_service.write_file(diagram_id, diagram_data)

            return NodeResult(
                success=True,
                node=updated_node,
                message=f"Updated node {input_data.id}",
            )

        except ValueError as e:
            logger.error(f"Validation error updating node: {e}")
            return NodeResult(success=False, error=f"Validation error: {e!s}")
        except Exception as e:
            logger.error(f"Failed to update node: {e}")
            return NodeResult(success=False, error=f"Failed to update node: {e!s}")

    @strawberry.mutation
    async def delete_node(self, node_id: NodeID, info) -> DeleteResult:
        """Removes node and connected elements."""
        try:
            context: GraphQLContext = info.context
            diagram_service = context.diagram_storage_service

            diagrams = await diagram_service.list_files()
            diagram_id = None
            diagram_data = None

            for diagram_meta in diagrams:
                temp_diagram = await diagram_service.read_file(diagram_meta.path)
                if node_id in temp_diagram.get("nodes", {}):
                    diagram_id = diagram_meta.path
                    diagram_data = temp_diagram
                    break

            if not diagram_data:
                return DeleteResult(
                    success=False, error=f"Node {node_id} not found in any diagram"
                )

            del diagram_data["nodes"][node_id]

            arrows_to_remove = []
            for arrow_id, arrow in diagram_data.get("arrows", {}).items():
                source_node_id = arrow["source"].split(":")[0]
                target_node_id = arrow["target"].split(":")[0]

                if source_node_id == node_id or target_node_id == node_id:
                    arrows_to_remove.append(arrow_id)

            for arrow_id in arrows_to_remove:
                del diagram_data["arrows"][arrow_id]

            handles_to_remove = []
            for handle_id, handle in diagram_data.get("handles", {}).items():
                if handle.get("nodeId") == node_id:
                    handles_to_remove.append(handle_id)

            for handle_id in handles_to_remove:
                del diagram_data["handles"][handle_id]

            await diagram_service.write_file(diagram_id, diagram_data)

            return DeleteResult(
                success=True,
                deleted_id=node_id,
                message=f"Deleted node {node_id} and {len(arrows_to_remove)} connected arrows",
            )

        except Exception as e:
            logger.error(f"Failed to delete node {node_id}: {e}")
            return DeleteResult(success=False, error=f"Failed to delete node: {e!s}")
