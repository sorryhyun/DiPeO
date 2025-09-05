"""CLI session mutations for GraphQL schema."""

import logging

import strawberry

from dipeo.application.execution.use_cases import CliSessionService
from dipeo.application.registry import CLI_SESSION_SERVICE, ServiceRegistry
from dipeo.diagram_generated.graphql.inputs import (
    RegisterCliSessionInput,
    UnregisterCliSessionInput,
)

from ...types.results import CliSessionResult

logger = logging.getLogger(__name__)


def create_cli_session_mutations(registry: ServiceRegistry) -> type:
    """Create CLI session mutation methods with injected service registry."""

    @strawberry.type
    class CliSessionMutations:
        @strawberry.mutation
        async def register_cli_session(self, input: RegisterCliSessionInput) -> CliSessionResult:
            """Register a new CLI execution session."""
            try:
                # Get or create CLI session service
                cli_session_service = registry.get(CLI_SESSION_SERVICE)
                if not cli_session_service:
                    cli_session_service = CliSessionService()
                    registry.register(CLI_SESSION_SERVICE, cli_session_service)

                # If diagram_data is not provided, try to load it from file
                diagram_data = input.diagram_data
                if diagram_data is None and (input.diagram_path or input.diagram_name):
                    # Use diagram_path if provided, otherwise fall back to diagram_name
                    diagram_path = input.diagram_path or input.diagram_name
                    try:
                        # Load diagram from file using the diagram service
                        from dipeo.application.registry.keys import DIAGRAM_PORT

                        diagram_service = registry.get(DIAGRAM_PORT)

                        if diagram_service:
                            # Initialize diagram service if needed
                            if hasattr(diagram_service, "initialize"):
                                await diagram_service.initialize()

                            # Use the provided path to load the diagram

                            # Load the diagram using the service
                            if hasattr(diagram_service, "load_from_file"):
                                domain_diagram = await diagram_service.load_from_file(diagram_path)
                            else:
                                # Fallback to getting diagram dict
                                diagram_dict = await diagram_service.get_diagram(diagram_path)
                                # Convert to DomainDiagram
                                from dipeo.infrastructure.diagram.adapters import (
                                    UnifiedSerializerAdapter,
                                )

                                serializer = UnifiedSerializerAdapter()
                                await serializer.initialize()
                                import json

                                json_content = json.dumps(diagram_dict)
                                domain_diagram = serializer.deserialize_from_storage(
                                    json_content, "native"
                                )

                            if domain_diagram:
                                # Convert DomainDiagram to dict for frontend
                                diagram_data = {
                                    "nodes": [
                                        node.model_dump(by_alias=True)
                                        for node in domain_diagram.nodes
                                    ],
                                    "handles": [
                                        handle.model_dump(by_alias=True)
                                        for handle in domain_diagram.handles
                                    ],
                                    "arrows": [
                                        {
                                            **arrow.model_dump(
                                                by_alias=True, exclude={"content_type"}
                                            ),
                                            "content_type": arrow.content_type.value
                                            if arrow.content_type
                                            and hasattr(arrow.content_type, "value")
                                            else str(arrow.content_type)
                                            if arrow.content_type
                                            else None,
                                        }
                                        for arrow in domain_diagram.arrows
                                    ],
                                    "persons": [
                                        person.model_dump(by_alias=True)
                                        for person in domain_diagram.persons
                                    ],
                                }
                                if domain_diagram.metadata:
                                    diagram_data["metadata"] = domain_diagram.metadata.model_dump(
                                        by_alias=True
                                    )
                            else:
                                logger.warning(f"Could not load diagram from file: {diagram_path}")
                        else:
                            logger.warning("Diagram service not available")
                    except Exception as e:
                        logger.warning(f"Could not load diagram from file: {e}", exc_info=True)

                # Register the session
                await cli_session_service.start_cli_session(
                    execution_id=input.execution_id,
                    diagram_name=input.diagram_name,
                    diagram_format=input.diagram_format,
                    diagram_data=diagram_data,
                )

                return CliSessionResult(
                    success=True,
                    message=f"CLI session registered for execution {input.execution_id}",
                )

            except Exception as e:
                logger.error(f"Failed to register CLI session: {e}")
                return CliSessionResult(
                    success=False, error=f"Failed to register CLI session: {e!s}"
                )

        @strawberry.mutation
        async def unregister_cli_session(
            self, input: UnregisterCliSessionInput
        ) -> CliSessionResult:
            """Unregister a CLI execution session."""
            try:
                cli_session_service = registry.get(CLI_SESSION_SERVICE)
                if not cli_session_service:
                    return CliSessionResult(
                        success=False, error="CLI session service not available"
                    )

                # Unregister the session
                success = await cli_session_service.end_cli_session(input.execution_id)

                if success:
                    return CliSessionResult(
                        success=True,
                        message=f"CLI session unregistered for execution {input.execution_id}",
                    )
                else:
                    return CliSessionResult(
                        success=False,
                        error=f"No active CLI session found for execution {input.execution_id}",
                    )

            except Exception as e:
                logger.error(f"Failed to unregister CLI session: {e}")
                return CliSessionResult(
                    success=False, error=f"Failed to unregister CLI session: {e!s}"
                )

    return CliSessionMutations
