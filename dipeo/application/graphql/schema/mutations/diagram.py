"""Diagram mutations using ServiceRegistry."""

import logging
from datetime import datetime

import strawberry
from strawberry.scalars import JSON

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_PORT
from dipeo.diagram_generated import DiagramMetadata, DomainDiagram
from dipeo.diagram_generated.domain_models import DiagramID
from dipeo.diagram_generated.graphql_backups.enums import DiagramFormatGraphQL
from dipeo.diagram_generated.graphql_backups.inputs import CreateDiagramInput
from dipeo.diagram_generated.graphql_backups.operations import (
    CREATE_DIAGRAM_MUTATION,
    DELETE_DIAGRAM_MUTATION,
    VALIDATE_DIAGRAM_MUTATION,
    CreateDiagramOperation,
    DeleteDiagramOperation,
    ValidateDiagramOperation,
)
from dipeo.diagram_generated.graphql_backups.results import DeleteResult, DiagramResult
from dipeo.infrastructure.diagram.adapters import UnifiedSerializerAdapter

logger = logging.getLogger(__name__)


# Standalone resolver functions for use with OperationExecutor
async def create_diagram(registry: ServiceRegistry, input: CreateDiagramInput) -> DiagramResult:
    """
    Resolver for CreateDiagram operation.
    Uses the generated CREATE_DIAGRAM_MUTATION query string.
    """
    try:
        diagram_service = registry.resolve(DIAGRAM_PORT)

        metadata = DiagramMetadata(
            name=input.name,
            description=input.description or "",
            author=input.author or "",
            tags=input.tags or [],
            created=datetime.now(),
            modified=datetime.now(),
        )

        diagram_model = DomainDiagram(
            nodes=[],
            arrows=[],
            handles=[],
            persons=[],
            apiKeys=[],
            metadata=metadata,
        )

        filename = await diagram_service.create_diagram(input.name, diagram_model, "json")

        return DiagramResult.success_result(
            data=diagram_model, message=f"Created diagram: {filename}"
        )

    except ValueError as e:
        logger.error(f"Validation error creating diagram: {e}")
        return DiagramResult.error_result(error=f"Validation error: {e!s}")
    except Exception as e:
        logger.error(f"Failed to create diagram: {e}")
        return DiagramResult.error_result(error=f"Failed to create diagram: {e!s}")


async def delete_diagram(registry: ServiceRegistry, diagram_id: strawberry.ID) -> DeleteResult:
    """
    Resolver for DeleteDiagram operation.
    Uses the generated DELETE_DIAGRAM_MUTATION query string.
    """
    try:
        diagram_id_typed = DiagramID(str(diagram_id))
        diagram_service = registry.resolve(DIAGRAM_PORT)

        diagram_data = await diagram_service.get_diagram(diagram_id_typed)
        if not diagram_data:
            raise FileNotFoundError(f"Diagram not found: {diagram_id}")

        file_repo = diagram_service.file_repository
        path = await file_repo.find_by_id(str(diagram_id))
        if path:
            await diagram_service.delete_diagram(path)
        else:
            raise FileNotFoundError(f"Diagram path not found: {diagram_id}")

        result = DeleteResult.success_result(
            data=None, message=f"Deleted diagram: {diagram_id_typed}"
        )
        result.deleted_id = str(diagram_id_typed)
        return result

    except Exception as e:
        logger.error(f"Failed to delete diagram {diagram_id_typed}: {e}")
        return DeleteResult.error_result(error=f"Failed to delete diagram: {e!s}")


async def validate_diagram(
    registry: ServiceRegistry, content: str, format: DiagramFormatGraphQL
) -> DiagramResult:
    """
    Resolver for ValidateDiagram operation.
    Uses the generated VALIDATE_DIAGRAM_MUTATION query string.
    """
    try:
        diagram_service = registry.resolve(DIAGRAM_PORT)
        serializer = UnifiedSerializerAdapter()
        await serializer.initialize()

        # Validate the provided content with the specified format
        # Convert enum to string value for the serializer
        format_str = format.value if hasattr(format, "value") else str(format)
        domain_diagram = serializer.deserialize_from_storage(content, format_str)

        if not domain_diagram:
            raise ValueError("Could not load diagram for validation")

        # Perform validation
        validation_errors = []
        validation_warnings = []

        # Check for required metadata
        if not domain_diagram.metadata or not domain_diagram.metadata.name:
            validation_errors.append("Diagram must have a name")

        # Check for start nodes
        start_nodes = [n for n in domain_diagram.nodes if n.type == "START"]
        if not start_nodes:
            validation_warnings.append("Diagram has no START node")
        elif len(start_nodes) > 1:
            validation_warnings.append(
                f"Diagram has {len(start_nodes)} START nodes, consider using only one"
            )

        # Check for unconnected nodes
        connected_nodes = set()
        for arrow in domain_diagram.arrows:
            connected_nodes.add(arrow.source_node_id)
            connected_nodes.add(arrow.target_node_id)

        all_node_ids = {n.id for n in domain_diagram.nodes}
        unconnected = all_node_ids - connected_nodes
        if unconnected:
            validation_warnings.append(
                f"Found {len(unconnected)} unconnected nodes: {', '.join(unconnected)}"
            )

        # Check for invalid arrow references
        for arrow in domain_diagram.arrows:
            if arrow.source_node_id not in all_node_ids:
                validation_errors.append(
                    f"Arrow references non-existent source node: {arrow.source_node_id}"
                )
            if arrow.target_node_id not in all_node_ids:
                validation_errors.append(
                    f"Arrow references non-existent target node: {arrow.target_node_id}"
                )

        # Check persons have API keys
        for person in domain_diagram.persons:
            if not person.api_key_id:
                validation_warnings.append(f"Person '{person.name}' has no API key assigned")

        if validation_errors:
            error_msg = "Validation failed: " + "; ".join(validation_errors)
            result = DiagramResult.error_result(error=error_msg)
            result.diagram = domain_diagram
            result.validation_errors = validation_errors
            result.validation_warnings = validation_warnings
            return result
        else:
            message = "Diagram is valid"
            if validation_warnings:
                message += f" (with {len(validation_warnings)} warnings)"
            result = DiagramResult.success_result(data=domain_diagram, message=message)
            result.diagram = domain_diagram
            result.validation_errors = []
            result.validation_warnings = validation_warnings
            return result

    except Exception as e:
        logger.error(f"Failed to validate diagram: {e}")
        return DiagramResult.error_result(error=f"Failed to validate diagram: {e!s}")


def create_diagram_mutations(registry: ServiceRegistry) -> type:
    """Create diagram mutation methods with injected registry."""

    @strawberry.type
    class DiagramMutations:
        @strawberry.mutation
        async def create_diagram(self, input: CreateDiagramInput) -> DiagramResult:
            """Mutation method that delegates to standalone resolver."""
            return await create_diagram(registry, input)

        @strawberry.mutation
        async def delete_diagram(self, diagram_id: strawberry.ID) -> DeleteResult:
            """Mutation method that delegates to standalone resolver."""
            return await delete_diagram(registry, diagram_id)

        @strawberry.mutation
        async def validate_diagram(
            self, content: str, format: DiagramFormatGraphQL
        ) -> DiagramResult:
            """Mutation method that delegates to standalone resolver."""
            return await validate_diagram(registry, content, format)

    return DiagramMutations
