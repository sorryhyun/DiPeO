"""Node mutations using ServiceRegistry with type-specific input handling."""

import logging
from typing import Any

import strawberry
from strawberry.scalars import JSON

from dipeo.application.graphql.node_registry import NodeTypeRegistry
from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_PORT
from dipeo.diagram_generated.graphql.enums import NodeTypeGraphQL
from dipeo.diagram_generated.graphql.inputs import CreateNodeInput, UpdateNodeInput, Vec2Input
from dipeo.diagram_generated.graphql.results import DeleteResult, NodeResult

logger = logging.getLogger(__name__)


# Standalone resolver functions for operation executor
async def create_node(
    registry: ServiceRegistry, diagram_id: strawberry.ID, input: CreateNodeInput
) -> NodeResult:
    """Create a new node in a diagram with type-specific validation."""
    try:
        integrated_service = registry.resolve(DIAGRAM_PORT)

        diagram_data = await integrated_service.get_diagram(diagram_id)
        if not diagram_data:
            raise ValueError(f"Diagram not found: {diagram_id}")

        # Convert string type to enum
        node_type = NodeTypeRegistry.get_node_type_from_string(input.type)
        if not node_type:
            return NodeResult.error_result(error=f"Unknown node type: {input.type}")

        # Validate node data against type-specific rules
        is_valid, error = NodeTypeRegistry.validate_node_data(node_type, input.data)
        if not is_valid:
            return NodeResult.error_result(error=f"Invalid node data: {error}")

        # Check for node-specific constraints
        if node_type == NodeTypeGraphQL.START:
            # Check if a start node already exists
            existing_start = next(
                (n for n in diagram_data.get("nodes", []) if n.get("type") == "start"), None
            )
            if existing_start:
                return NodeResult.error_result(error="Diagram already has a start node")

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


async def update_node(
    registry: ServiceRegistry,
    diagram_id: strawberry.ID,
    node_id: strawberry.ID,
    input: UpdateNodeInput,
) -> NodeResult:
    """Update an existing node in a diagram with type-specific validation."""
    try:
        integrated_service = registry.resolve(DIAGRAM_PORT)

        diagram_data = await integrated_service.get_diagram(diagram_id)
        if not diagram_data:
            raise ValueError(f"Diagram not found: {diagram_id}")

        # Find and update the node
        nodes = diagram_data.get("nodes", [])
        node_found = False
        updated_node = None

        for _i, node in enumerate(nodes):
            if node.get("id") == node_id:
                node_found = True

                # Determine the node type (use existing type or new type if being changed)
                node_type_str = input.type if input.type else node.get("type")
                node_type = NodeTypeRegistry.get_node_type_from_string(node_type_str)

                if not node_type:
                    return NodeResult.error_result(error=f"Unknown node type: {node_type_str}")

                # Validate data if provided
                if input.data is not None:
                    is_valid, error = NodeTypeRegistry.validate_node_data(node_type, input.data)
                    if not is_valid:
                        return NodeResult.error_result(error=f"Invalid node data: {error}")

                # Check for type-specific constraints when changing type
                if input.type and input.type != node.get("type"):
                    if node_type == NodeTypeGraphQL.START:
                        # Check if a start node already exists
                        existing_start = next(
                            (
                                n
                                for n in nodes
                                if n.get("type") == "start" and n.get("id") != node_id
                            ),
                            None,
                        )
                        if existing_start:
                            return NodeResult.error_result(error="Diagram already has a start node")

                # Update node properties
                if input.position:
                    node["position"] = {"x": input.position.x, "y": input.position.y}
                if input.data is not None:
                    node["data"] = input.data
                if input.type:
                    node["type"] = input.type
                updated_node = node
                break

        if not node_found:
            return NodeResult.error_result(error=f"Node not found: {node_id}")

        # TODO: Save updated diagram back to storage

        return NodeResult.success_result(
            data=updated_node,
            message=f"Updated node: {node_id}",
        )

    except Exception as e:
        logger.error(f"Failed to update node {node_id}: {e}")
        return NodeResult.error_result(error=f"Failed to update node: {e!s}")


async def delete_node(
    registry: ServiceRegistry, diagram_id: strawberry.ID, node_id: strawberry.ID
) -> DeleteResult:
    """Delete a node from a diagram."""
    try:
        integrated_service = registry.resolve(DIAGRAM_PORT)

        diagram_data = await integrated_service.get_diagram(diagram_id)
        if not diagram_data:
            raise ValueError(f"Diagram not found: {diagram_id}")

        # Remove the node
        nodes = diagram_data.get("nodes", [])
        original_count = len(nodes)
        diagram_data["nodes"] = [node for node in nodes if node.get("id") != node_id]

        if len(diagram_data["nodes"]) == original_count:
            return DeleteResult.error_result(error=f"Node not found: {node_id}")

        # Also remove any arrows connected to this node
        if "arrows" in diagram_data:
            diagram_data["arrows"] = [
                arrow
                for arrow in diagram_data["arrows"]
                if arrow.get("source_node_id") != node_id and arrow.get("target_node_id") != node_id
            ]

        # TODO: Save updated diagram back to storage

        result = DeleteResult.success_result(data=None, message=f"Deleted node: {node_id}")
        result.deleted_id = node_id
        return result

    except Exception as e:
        logger.error(f"Failed to delete node {node_id}: {e}")
        return DeleteResult.error_result(error=f"Failed to delete node: {e!s}")


def create_node_mutations(registry: ServiceRegistry) -> type:
    """Create node mutation methods with injected registry and type-specific validation."""

    @strawberry.type
    class NodeMutations:
        @strawberry.mutation
        async def create_node(
            self, diagram_id: strawberry.ID, input: CreateNodeInput
        ) -> NodeResult:
            """Create a new node with type-specific validation."""
            try:
                integrated_service = registry.resolve(DIAGRAM_PORT)

                diagram_data = await integrated_service.get_diagram(diagram_id)
                if not diagram_data:
                    raise ValueError(f"Diagram not found: {diagram_id}")

                # Convert string type to enum
                node_type = NodeTypeRegistry.get_node_type_from_string(input.type)
                if not node_type:
                    return NodeResult.error_result(error=f"Unknown node type: {input.type}")

                # Validate node data against type-specific rules
                is_valid, error = NodeTypeRegistry.validate_node_data(node_type, input.data)
                if not is_valid:
                    return NodeResult.error_result(error=f"Invalid node data: {error}")

                # Check for node-specific constraints
                if node_type == NodeTypeGraphQL.START:
                    # Check if a start node already exists
                    existing_start = next(
                        (n for n in diagram_data.get("nodes", []) if n.get("type") == "start"), None
                    )
                    if existing_start:
                        return NodeResult.error_result(error="Diagram already has a start node")

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
            """Update a node with type-specific validation."""
            # Delegate to the standalone resolver function
            return await update_node(diagram_id, node_id, input, registry)

        @strawberry.mutation
        async def delete_node(
            self, diagram_id: strawberry.ID, node_id: strawberry.ID
        ) -> DeleteResult:
            """Delete a node from a diagram."""
            # Delegate to the standalone resolver function
            return await delete_node(diagram_id, node_id, registry)

        # Type-specific mutation methods for better type safety
        @strawberry.mutation
        async def create_person_job_node(
            self,
            diagram_id: strawberry.ID,
            person_id: str,
            message: str,
            position_x: float,
            position_y: float,
            variables: JSON | None = None,
            model: str | None = None,
            max_tokens: int | None = None,
        ) -> NodeResult:
            """Create a person_job node with validated inputs."""
            data = {
                "person_id": person_id,
                "message": message,
            }
            if variables:
                data["variables"] = variables
            if model:
                data["model"] = model
            if max_tokens:
                data["max_tokens"] = max_tokens

            input = CreateNodeInput(
                type="person_job", position=Vec2Input(x=position_x, y=position_y), data=data
            )
            return await self.create_node(diagram_id, input)

        @strawberry.mutation
        async def create_api_job_node(
            self,
            diagram_id: strawberry.ID,
            api_id: str,
            position_x: float,
            position_y: float,
            parameters: JSON | None = None,
            headers: JSON | None = None,
        ) -> NodeResult:
            """Create an api_job node with validated inputs."""
            data = {"api_id": api_id}
            if parameters:
                data["parameters"] = parameters
            if headers:
                data["headers"] = headers

            input = CreateNodeInput(
                type="api_job", position=Vec2Input(x=position_x, y=position_y), data=data
            )
            return await self.create_node(diagram_id, input)

        @strawberry.mutation
        async def create_condition_node(
            self,
            diagram_id: strawberry.ID,
            operator: str,
            position_x: float,
            position_y: float,
            value_b: JSON | None = None,
            combine_operator: str | None = None,
        ) -> NodeResult:
            """Create a condition node with validated inputs."""
            data = {"operator": operator}
            if value_b is not None:
                data["value_b"] = value_b
            if combine_operator:
                data["combine_operator"] = combine_operator

            input = CreateNodeInput(
                type="condition", position=Vec2Input(x=position_x, y=position_y), data=data
            )
            return await self.create_node(diagram_id, input)

    return NodeMutations
