"""Node mutations using ServiceRegistry."""

import logging

import strawberry

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_PORT
from dipeo.diagram_generated.graphql.inputs import CreateNodeInput, UpdateNodeInput
from dipeo.diagram_generated.graphql.results import DeleteResult, NodeResult

logger = logging.getLogger(__name__)


def create_node_mutations(registry: ServiceRegistry) -> type:
    """Create node mutation methods with injected registry.

    Simplified implementation - consider type-specific mutations for better type safety.
    """

    @strawberry.type
    class NodeMutations:
        @strawberry.mutation
        async def create_node(
            self, diagram_id: strawberry.ID, input: CreateNodeInput
        ) -> NodeResult:
            try:
                integrated_service = registry.resolve(DIAGRAM_PORT)

                diagram_data = await integrated_service.get_diagram(diagram_id)
                if not diagram_data:
                    raise ValueError(f"Diagram not found: {diagram_id}")

                node_id = f"node_{len(diagram_data.get('nodes', []))}"
                node = {
                    "id": node_id,
                    "type": input.type,
                    "position": {"x": input.position.x, "y": input.position.y},
                    "data": input.data,
                }

                if "nodes" not in diagram_data:
                    diagram_data["nodes"] = []
                diagram_data["nodes"].append(node)

                return NodeResult.success_result(data=node, message=f"Created node: {node_id}")

            except Exception as e:
                logger.error(f"Failed to create node: {e}")
                return NodeResult.error_result(error=f"Failed to create node: {e!s}")

        @strawberry.mutation
        async def update_node(
            self, diagram_id: strawberry.ID, node_id: strawberry.ID, input: UpdateNodeInput
        ) -> NodeResult:
            try:
                return NodeResult.success_result(
                    data=None,  # TODO: return updated node
                    message=f"Updated node: {node_id}",
                )

            except Exception as e:
                logger.error(f"Failed to update node {node_id}: {e}")
                return NodeResult.error_result(error=f"Failed to update node: {e!s}")

        @strawberry.mutation
        async def delete_node(
            self, diagram_id: strawberry.ID, node_id: strawberry.ID
        ) -> DeleteResult:
            try:
                result = DeleteResult.success_result(data=None, message=f"Deleted node: {node_id}")
                result.deleted_id = node_id
                return result

            except Exception as e:
                logger.error(f"Failed to delete node {node_id}: {e}")
                return DeleteResult.error_result(error=f"Failed to delete node: {e!s}")

    return NodeMutations
