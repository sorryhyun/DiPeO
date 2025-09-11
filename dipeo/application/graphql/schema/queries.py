"""GraphQL queries for DiPeO.

These queries use the ServiceRegistry to access application services,
keeping GraphQL concerns separate from business logic.
"""

from datetime import datetime
from pathlib import Path

import strawberry
from strawberry.scalars import JSON

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import (
    CLI_SESSION_SERVICE,
    DIAGRAM_CONVERTER,
    DIAGRAM_PORT,
    EXECUTION_ORCHESTRATOR,
    FILESYSTEM_ADAPTER,
    STATE_STORE,
)
from dipeo.config import FILES_DIR
from dipeo.diagram_generated import LLMService, NodeType

# Import domain models for type hints
from dipeo.diagram_generated.domain_models import ApiKeyID, DiagramID, ExecutionID, PersonID

# Import Strawberry types
from dipeo.diagram_generated.graphql.domain_types import (
    DomainApiKeyType,
    DomainDiagramType,
    DomainPersonType,
    ExecutionStateType,
)
from dipeo.diagram_generated.graphql.inputs import DiagramFilterInput, ExecutionFilterInput

# Import ID scalars as Strawberry scalars
from ..resolvers import DiagramResolver, ExecutionResolver, PersonResolver
from ..resolvers.provider_resolver import ProviderResolver
from ..types.cli_session import CliSession
from ..types.provider_types import (
    OperationSchemaType,
    OperationType,
    ProviderStatisticsType,
    ProviderType,
)
from ..types.query_types import DiagramFormatInfo

DIAGRAM_VERSION = "1.0.0"


def create_query_type(registry: ServiceRegistry) -> type:
    """Create Query type with injected service registry."""
    diagram_resolver = DiagramResolver(registry)
    execution_resolver = ExecutionResolver(registry)
    person_resolver = PersonResolver(registry)
    provider_resolver = ProviderResolver(registry)

    @strawberry.type
    class Query:
        @strawberry.field
        async def diagram(self, id: strawberry.ID) -> DomainDiagramType | None:
            diagram_id = DiagramID(str(id))
            return await diagram_resolver.get_diagram(diagram_id)

        @strawberry.field
        async def diagrams(
            self,
            filter: DiagramFilterInput | None = None,
            limit: int = 100,
            offset: int = 0,
        ) -> list[DomainDiagramType]:
            return await diagram_resolver.list_diagrams(filter, limit, offset)

        @strawberry.field
        async def execution(self, id: strawberry.ID) -> ExecutionStateType | None:
            execution_id = ExecutionID(str(id))
            return await execution_resolver.get_execution(execution_id)

        @strawberry.field
        async def executions(
            self,
            filter: ExecutionFilterInput | None = None,
            limit: int = 100,
            offset: int = 0,
        ) -> list[ExecutionStateType]:
            return await execution_resolver.list_executions(filter, limit, offset)

        @strawberry.field
        async def person(self, id: strawberry.ID) -> DomainPersonType | None:
            person_id = PersonID(str(id))
            return await person_resolver.get_person(person_id)

        @strawberry.field
        async def persons(self, limit: int = 100) -> list[DomainPersonType]:
            return await person_resolver.list_persons(limit)

        @strawberry.field
        async def api_key(self, id: strawberry.ID) -> DomainApiKeyType | None:
            api_key_id = ApiKeyID(str(id))
            return await person_resolver.get_api_key(api_key_id)

        @strawberry.field
        async def api_keys(self, service: str | None = None) -> list[DomainApiKeyType]:
            return await person_resolver.list_api_keys(service)

        @strawberry.field
        async def available_models(self, service: str, api_key_id: strawberry.ID) -> list[str]:
            api_key_id_typed = ApiKeyID(str(api_key_id))
            return await person_resolver.get_available_models(service, api_key_id_typed)

        @strawberry.field
        async def providers(self) -> list[ProviderType]:
            return await provider_resolver.list_providers()

        @strawberry.field
        async def provider(self, name: str) -> ProviderType | None:
            return await provider_resolver.get_provider(name)

        @strawberry.field
        async def provider_operations(self, provider: str) -> list[OperationType]:
            return await provider_resolver.get_provider_operations(provider)

        @strawberry.field
        async def operation_schema(
            self, provider: str, operation: str
        ) -> OperationSchemaType | None:
            return await provider_resolver.get_operation_schema(provider, operation)

        @strawberry.field
        async def provider_statistics(self) -> ProviderStatisticsType:
            return await provider_resolver.get_provider_statistics()

        @strawberry.field
        async def system_info(self) -> JSON:
            return {
                "version": DIAGRAM_VERSION,
                "supported_node_types": [t.value for t in NodeType],
                "supported_llm_services": [s.value for s in LLMService],
                "max_upload_size_mb": 100,
                "graphql_subscriptions_enabled": True,
            }

        @strawberry.field
        async def execution_capabilities(self) -> JSON:
            integrated_service = registry.resolve(DIAGRAM_PORT)
            persons_list = []

            if integrated_service:
                diagram_infos = await integrated_service.list_diagrams()
                for diagram_info in diagram_infos:
                    path = diagram_info.get("path", "")
                    diagram_id = path.split(".")[0] if path else diagram_info.get("id")
                    diagram = await integrated_service.get_diagram(diagram_id)
                    for person_id, person_data in diagram.get("persons", {}).items():
                        persons_list.append(
                            {
                                "id": person_id,
                                "name": person_data.get("name", ""),
                                "model": person_data.get("modelName", "gpt-4o-mini"),
                                "apiKeyId": person_data.get("apiKeyId"),
                            }
                        )

            return {
                "supported_node_types": [t.value for t in NodeType],
                "supported_llm_services": [s.value for s in LLMService],
                "available_persons": persons_list,
                "execution_features": {
                    "interactive_prompts": True,
                    "pause_resume": True,
                    "node_skip": True,
                    "real_time_updates": True,
                    "token_tracking": True,
                },
            }

        @strawberry.field
        async def health(self) -> JSON:
            checks = {"database": False, "redis": False, "file_system": False}

            try:
                state_store = registry.resolve(STATE_STORE)
                if state_store:
                    await state_store.list_executions(limit=1)
                    checks["database"] = True
            except Exception:
                pass

            checks["redis"] = False

            try:
                (FILES_DIR / "diagrams").exists()
                checks["file_system"] = True
            except Exception:
                pass

            all_healthy = all(checks.values())

            return {
                "status": "healthy" if all_healthy else "degraded",
                "timestamp": datetime.now().isoformat(),
                "checks": checks,
                "version": DIAGRAM_VERSION,
            }

        @strawberry.field
        async def conversations(
            self,
            person_id: strawberry.ID | None = None,
            execution_id: strawberry.ID | None = None,
            search: str | None = None,
            show_forgotten: bool = False,
            limit: int = 100,
            offset: int = 0,
            since: datetime | None = None,
        ) -> JSON:
            conversation_service = registry.resolve(EXECUTION_ORCHESTRATOR)

            if not conversation_service or not hasattr(
                conversation_service, "person_conversations"
            ):
                return {
                    "conversations": [],
                    "total": 0,
                    "limit": limit,
                    "offset": offset,
                    "has_more": False,
                }

            return {
                "conversations": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
            }

        @strawberry.field
        async def supported_formats(self) -> list[DiagramFormatInfo]:
            converter = registry.resolve(DIAGRAM_CONVERTER)
            formats = converter.list_formats()
            return [
                DiagramFormatInfo(
                    format=fmt["id"],
                    name=fmt["name"],
                    description=fmt.get("description", ""),
                    extension=fmt["extension"],
                    supports_import=fmt.get("supports_import", True),
                    supports_export=fmt.get("supports_export", True),
                )
                for fmt in formats
            ]

        @strawberry.field
        async def execution_order(self, execution_id: strawberry.ID) -> JSON:
            execution_id_typed = ExecutionID(str(execution_id))
            execution = await execution_resolver.get_execution(execution_id_typed)
            if not execution:
                return {
                    "executionId": str(execution_id_typed),
                    "nodes": [],
                    "error": "Execution not found",
                    "status": "NOT_FOUND",
                    "totalNodes": 0,
                }

            nodes = []
            executed_nodes = (
                execution.executed_nodes if hasattr(execution, "executed_nodes") else []
            )
            node_states = execution.node_states if hasattr(execution, "node_states") else {}
            for node_id in executed_nodes:
                if node_id in node_states:
                    node_state = node_states[node_id]

                    # Build node step data
                    node_step = {
                        "nodeId": node_id,
                        "nodeName": node_id,  # Use node ID as name (could be enhanced with label lookup)
                        "status": str(node_state.status)
                        if hasattr(node_state, "status")
                        else "UNKNOWN",
                    }

                    # Add timestamps if available
                    if hasattr(node_state, "started_at") and node_state.started_at:
                        node_step["startedAt"] = node_state.started_at

                    if hasattr(node_state, "ended_at") and node_state.ended_at:
                        node_step["endedAt"] = node_state.ended_at

                        # Calculate duration if both timestamps exist
                        if hasattr(node_state, "started_at") and node_state.started_at:
                            try:
                                from datetime import datetime

                                start = datetime.fromisoformat(
                                    node_state.started_at.replace("Z", "+00:00")
                                )
                                end = datetime.fromisoformat(
                                    node_state.ended_at.replace("Z", "+00:00")
                                )
                                duration_ms = int((end - start).total_seconds() * 1000)
                                node_step["duration"] = duration_ms
                            except Exception:
                                pass

                    # Add error if present
                    if hasattr(node_state, "error") and node_state.error:
                        node_step["error"] = node_state.error

                    # Add token usage if available
                    if hasattr(node_state, "token_usage") and node_state.token_usage:
                        token_usage = node_state.token_usage
                        node_step["tokenUsage"] = {
                            "input": token_usage.input_tokens
                            if hasattr(token_usage, "input_tokens")
                            else 0,
                            "output": token_usage.output_tokens
                            if hasattr(token_usage, "output_tokens")
                            else 0,
                            "cached": token_usage.cached_tokens
                            if hasattr(token_usage, "cached_tokens")
                            else 0,
                            "total": token_usage.total_tokens
                            if hasattr(token_usage, "total_tokens")
                            else 0,
                        }

                    nodes.append(node_step)

            # Return complete execution order data
            result = {
                "executionId": str(execution_id_typed),
                "status": str(execution.status) if hasattr(execution, "status") else "UNKNOWN",
                "nodes": nodes,
                "totalNodes": len(nodes),
            }

            # Add execution timestamps if available
            if hasattr(execution, "started_at") and execution.started_at:
                result["startedAt"] = execution.started_at

            if hasattr(execution, "ended_at") and execution.ended_at:
                result["endedAt"] = execution.ended_at

            return result

        @strawberry.field
        async def prompt_files(self) -> list[JSON]:
            filesystem = registry.get(FILESYSTEM_ADAPTER)
            if not filesystem:
                return []

            prompts_dir = Path(FILES_DIR) / "prompts"
            if not filesystem.exists(prompts_dir):
                return []

            prompt_files = []
            valid_extensions = {".txt", ".md", ".csv", ".json", ".yaml"}

            for item in filesystem.listdir(prompts_dir):
                if item.suffix in valid_extensions:
                    try:
                        file_info = filesystem.stat(prompts_dir / item.name)
                        prompt_files.append(
                            {
                                "name": item.name,
                                "path": str(item.relative_to(prompts_dir)),
                                "extension": item.suffix[1:],
                                "size": file_info.size,
                            }
                        )
                    except Exception as e:
                        import logging

                        logging.warning(f"Failed to process prompt file {item}: {e}")

            return prompt_files

        @strawberry.field
        async def prompt_file(self, filename: str) -> JSON:
            filesystem = registry.get(FILESYSTEM_ADAPTER)
            if not filesystem:
                return {
                    "success": False,
                    "error": "Filesystem adapter not available",
                    "filename": filename,
                }

            prompts_dir = Path(FILES_DIR) / "prompts"
            file_path = prompts_dir / filename

            if not filesystem.exists(file_path):
                return {
                    "success": False,
                    "error": f"Prompt file not found: {filename}",
                    "filename": filename,
                }

            try:
                with filesystem.open(file_path, "rb") as f:
                    raw_content = f.read()
                    content = raw_content.decode("utf-8")

                file_info = filesystem.stat(file_path)

                return {
                    "success": True,
                    "filename": filename,
                    "content": content,
                    "raw_content": content,  # Keep both for compatibility
                    "extension": file_path.suffix[1:],
                    "size": file_info.size,
                }
            except Exception as e:
                import logging

                logging.error(f"Failed to read prompt file {filename}: {e}")
                return {
                    "success": False,
                    "error": f"Failed to read file: {e!s}",
                    "filename": filename,
                }

        @strawberry.field
        async def active_cli_session(self) -> CliSession | None:
            cli_session_service = registry.resolve(CLI_SESSION_SERVICE)
            if not cli_session_service:
                return None

            from dipeo.application.execution.use_cases import CliSessionService

            if isinstance(cli_session_service, CliSessionService):
                session_data = await cli_session_service.get_active_session()
                if session_data:
                    # Convert internal CliSessionData to GraphQL CliSession
                    return CliSession(
                        execution_id=session_data.execution_id,
                        diagram_name=session_data.diagram_name,
                        diagram_format=session_data.diagram_format,
                        started_at=session_data.started_at,
                        is_active=session_data.is_active,
                        diagram_data=session_data.diagram_data,
                        node_states=session_data.node_states,  # Include initial node states
                    )

            return None

        @strawberry.field
        async def execution_metrics(self, execution_id: strawberry.ID) -> JSON | None:
            from dipeo.application.execution.observers import MetricsObserver
            from dipeo.application.registry.keys import ServiceKey

            execution_id_typed = ExecutionID(str(execution_id))

            # Try to get metrics from MetricsObserver first (real-time data)
            try:
                metrics_observer_key = ServiceKey[MetricsObserver]("metrics_observer")
                metrics_observer = registry.resolve(metrics_observer_key)

                # Get detailed metrics summary from observer
                metrics_summary = metrics_observer.get_metrics_summary(str(execution_id))
                if metrics_summary:
                    # Get individual node metrics for detailed breakdown
                    execution_metrics = metrics_observer.get_execution_metrics(str(execution_id))
                    if execution_metrics:
                        node_breakdown = []
                        for node_id, node_metrics in execution_metrics.node_metrics.items():
                            node_data = {
                                "node_id": node_id,
                                "node_type": node_metrics.node_type,
                                "duration_ms": node_metrics.duration_ms,
                                "token_usage": node_metrics.token_usage
                                or {"input": 0, "output": 0, "total": 0},
                                "error": node_metrics.error,
                            }
                            node_breakdown.append(node_data)

                        metrics_summary["node_breakdown"] = node_breakdown

                    return metrics_summary
            except Exception:
                pass  # Fall back to execution state

            # Fall back to execution state if observer doesn't have data
            execution = await execution_resolver.get_execution(execution_id_typed)
            if not execution or not hasattr(execution, "metrics"):
                return None

            return execution.metrics

        @strawberry.field
        async def execution_history(
            self,
            diagram_id: strawberry.ID | None = None,
            limit: int = 100,
            include_metrics: bool = False,
        ) -> list[ExecutionStateType]:
            filter_input = None
            if diagram_id:
                filter_input = ExecutionFilterInput(diagram_id=DiagramID(str(diagram_id)))

            executions = await execution_resolver.list_executions(
                filter=filter_input, limit=limit, offset=0
            )

            # If not including metrics, clear them from results
            if not include_metrics:
                for execution in executions:
                    if hasattr(execution, "metrics"):
                        execution.metrics = None

            return executions

    return Query
