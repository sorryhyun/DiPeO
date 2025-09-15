"""Standalone query resolver functions for use with OperationExecutor.

These resolvers are extracted from the Query class to support the operation-based architecture.
Each resolver function takes a ServiceRegistry as its first parameter.
"""

import logging
from datetime import datetime
from pathlib import Path

import strawberry
from strawberry.scalars import JSON

from dipeo.application.graphql.resolvers import DiagramResolver, ExecutionResolver, PersonResolver
from dipeo.application.graphql.resolvers.provider_resolver import ProviderResolver
from dipeo.application.graphql.types.cli_session import CliSession
from dipeo.application.graphql.types.provider_types import (
    OperationSchemaType,
    OperationType,
    ProviderStatisticsType,
    ProviderType,
)
from dipeo.application.graphql.types.query_types import DiagramFormatInfo
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
from dipeo.diagram_generated.domain_models import ApiKeyID, DiagramID, ExecutionID, PersonID
from dipeo.diagram_generated.graphql.domain_types import (
    DomainApiKeyType,
    DomainDiagramType,
    DomainPersonType,
    ExecutionStateType,
)
from dipeo.diagram_generated.graphql.inputs import DiagramFilterInput, ExecutionFilterInput

logger = logging.getLogger(__name__)
DIAGRAM_VERSION = "1.0.0"


# Query resolvers - Diagrams
async def get_diagram(
    registry: ServiceRegistry, diagram_id: strawberry.ID
) -> DomainDiagramType | None:
    """Get a single diagram by ID."""
    diagram_resolver = DiagramResolver(registry)
    diagram_id_typed = DiagramID(str(diagram_id))
    return await diagram_resolver.get_diagram(diagram_id_typed)


async def list_diagrams(
    registry: ServiceRegistry,
    filter: DiagramFilterInput | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[DomainDiagramType]:
    """List diagrams with optional filtering."""
    diagram_resolver = DiagramResolver(registry)
    return await diagram_resolver.list_diagrams(filter, limit, offset)


# Query resolvers - Executions
async def get_execution(
    registry: ServiceRegistry, execution_id: strawberry.ID
) -> ExecutionStateType | None:
    """Get a single execution by ID."""
    execution_resolver = ExecutionResolver(registry)
    execution_id_typed = ExecutionID(str(execution_id))
    return await execution_resolver.get_execution(execution_id_typed)


async def list_executions(
    registry: ServiceRegistry,
    filter: ExecutionFilterInput | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ExecutionStateType]:
    """List executions with optional filtering."""
    execution_resolver = ExecutionResolver(registry)
    return await execution_resolver.list_executions(filter, limit, offset)


async def get_execution_order(registry: ServiceRegistry, execution_id: strawberry.ID) -> JSON:
    """Get the execution order for a given execution."""
    execution_resolver = ExecutionResolver(registry)
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
    executed_nodes = execution.executed_nodes if hasattr(execution, "executed_nodes") else []
    node_states = execution.node_states if hasattr(execution, "node_states") else {}

    for node_id in executed_nodes:
        if node_id in node_states:
            node_state = node_states[node_id]

            node_step = {
                "nodeId": node_id,
                "nodeName": node_id,
                "status": str(node_state.status) if hasattr(node_state, "status") else "UNKNOWN",
            }

            if hasattr(node_state, "started_at") and node_state.started_at:
                node_step["startedAt"] = node_state.started_at

            if hasattr(node_state, "ended_at") and node_state.ended_at:
                node_step["endedAt"] = node_state.ended_at

                if hasattr(node_state, "started_at") and node_state.started_at:
                    try:
                        start = datetime.fromisoformat(node_state.started_at.replace("Z", "+00:00"))
                        end = datetime.fromisoformat(node_state.ended_at.replace("Z", "+00:00"))
                        duration_ms = int((end - start).total_seconds() * 1000)
                        node_step["duration"] = duration_ms
                    except Exception:
                        pass

            if hasattr(node_state, "error") and node_state.error:
                node_step["error"] = node_state.error

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

    result = {
        "executionId": str(execution_id_typed),
        "status": str(execution.status) if hasattr(execution, "status") else "UNKNOWN",
        "nodes": nodes,
        "totalNodes": len(nodes),
    }

    if hasattr(execution, "started_at") and execution.started_at:
        result["startedAt"] = execution.started_at

    if hasattr(execution, "ended_at") and execution.ended_at:
        result["endedAt"] = execution.ended_at

    return result


async def get_execution_metrics(
    registry: ServiceRegistry, execution_id: strawberry.ID
) -> JSON | None:
    """Get metrics for a given execution."""
    from dipeo.application.execution.observers import MetricsObserver
    from dipeo.application.registry.keys import ServiceKey

    execution_resolver = ExecutionResolver(registry)
    execution_id_typed = ExecutionID(str(execution_id))

    try:
        metrics_observer_key = ServiceKey[MetricsObserver]("metrics_observer")
        metrics_observer = registry.resolve(metrics_observer_key)

        metrics_summary = metrics_observer.get_metrics_summary(str(execution_id))
        if metrics_summary:
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
        pass

    execution = await execution_resolver.get_execution(execution_id_typed)
    if not execution or not hasattr(execution, "metrics"):
        return {}

    return execution.metrics or {}


async def get_execution_history(
    registry: ServiceRegistry,
    diagram_id: strawberry.ID | None = None,
    limit: int = 100,
    include_metrics: bool = False,
) -> list[ExecutionStateType]:
    """Get execution history with optional filtering."""
    execution_resolver = ExecutionResolver(registry)
    filter_input = None
    if diagram_id:
        filter_input = ExecutionFilterInput(diagram_id=DiagramID(str(diagram_id)))

    executions = await execution_resolver.list_executions(
        filter=filter_input, limit=limit, offset=0
    )

    if not include_metrics:
        for execution in executions:
            if hasattr(execution, "metrics"):
                execution.metrics = None

    return executions


# Query resolvers - Persons
async def get_person(
    registry: ServiceRegistry, person_id: strawberry.ID
) -> DomainPersonType | None:
    """Get a single person by ID."""
    person_resolver = PersonResolver(registry)
    person_id_typed = PersonID(str(person_id))
    return await person_resolver.get_person(person_id_typed)


async def list_persons(registry: ServiceRegistry, limit: int = 100) -> list[DomainPersonType]:
    """List all persons."""
    person_resolver = PersonResolver(registry)
    return await person_resolver.list_persons(limit)


# Query resolvers - API Keys
async def get_api_key(
    registry: ServiceRegistry, api_key_id: strawberry.ID
) -> DomainApiKeyType | None:
    """Get a single API key by ID."""
    person_resolver = PersonResolver(registry)
    api_key_id_typed = ApiKeyID(str(api_key_id))
    return await person_resolver.get_api_key(api_key_id_typed)


async def get_api_keys(
    registry: ServiceRegistry, service: str | None = None
) -> list[DomainApiKeyType]:
    """List API keys, optionally filtered by service."""
    person_resolver = PersonResolver(registry)
    return await person_resolver.list_api_keys(service)


async def get_available_models(
    registry: ServiceRegistry, service: str, api_key_id: strawberry.ID
) -> list[str]:
    """Get available models for a given service and API key."""
    person_resolver = PersonResolver(registry)
    api_key_id_typed = ApiKeyID(str(api_key_id))
    return await person_resolver.get_available_models(service, api_key_id_typed)


# Query resolvers - Providers
async def get_providers(registry: ServiceRegistry) -> list[ProviderType]:
    """List all providers."""
    provider_resolver = ProviderResolver(registry)
    return await provider_resolver.list_providers()


async def get_provider(registry: ServiceRegistry, name: str) -> ProviderType | None:
    """Get a single provider by name."""
    provider_resolver = ProviderResolver(registry)
    return await provider_resolver.get_provider(name)


async def get_provider_operations(registry: ServiceRegistry, provider: str) -> list[OperationType]:
    """Get operations for a specific provider."""
    provider_resolver = ProviderResolver(registry)
    return await provider_resolver.get_provider_operations(provider)


async def get_operation_schema(
    registry: ServiceRegistry, provider: str, operation: str
) -> OperationSchemaType | None:
    """Get schema for a specific operation."""
    provider_resolver = ProviderResolver(registry)
    return await provider_resolver.get_operation_schema(provider, operation)


async def get_provider_statistics(registry: ServiceRegistry) -> ProviderStatisticsType:
    """Get provider statistics."""
    provider_resolver = ProviderResolver(registry)
    return await provider_resolver.get_provider_statistics()


# Query resolvers - System
async def get_system_info(registry: ServiceRegistry) -> JSON:
    """Get system information."""
    return {
        "version": DIAGRAM_VERSION,
        "supported_node_types": [t.value for t in NodeType],
        "supported_llm_services": [s.value for s in LLMService],
        "max_upload_size_mb": 100,
        "graphql_subscriptions_enabled": True,
    }


async def get_execution_capabilities(registry: ServiceRegistry) -> JSON:
    """Get execution capabilities including available persons."""
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


async def health_check(registry: ServiceRegistry) -> JSON:
    """Check system health."""
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


async def list_conversations(
    registry: ServiceRegistry,
    person_id: strawberry.ID | None = None,
    execution_id: strawberry.ID | None = None,
    search: str | None = None,
    show_forgotten: bool = False,
    limit: int = 100,
    offset: int = 0,
    since: datetime | None = None,
) -> list[JSON]:
    """List conversations with optional filtering."""
    conversation_service = registry.resolve(EXECUTION_ORCHESTRATOR)

    if not conversation_service or not hasattr(conversation_service, "person_conversations"):
        return []

    # Return empty list for now - full implementation pending
    return []


async def get_supported_formats(registry: ServiceRegistry) -> list[DiagramFormatInfo]:
    """Get supported diagram formats."""
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


async def list_prompt_files(registry: ServiceRegistry) -> list[JSON]:
    """List available prompt files."""
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
                logger.warning(f"Failed to process prompt file {item}: {e}")

    return prompt_files


async def get_prompt_file(registry: ServiceRegistry, filename: str) -> JSON:
    """Get a specific prompt file."""
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
            "raw_content": content,
            "extension": file_path.suffix[1:],
            "size": file_info.size,
        }
    except Exception as e:
        logger.error(f"Failed to read prompt file {filename}: {e}")
        return {
            "success": False,
            "error": f"Failed to read file: {e!s}",
            "filename": filename,
        }


async def get_active_cli_session(registry: ServiceRegistry) -> dict:
    """Get the active CLI session if any."""
    cli_session_service = registry.resolve(CLI_SESSION_SERVICE)
    if not cli_session_service:
        return {}

    from dipeo.application.execution.use_cases import CliSessionService

    if isinstance(cli_session_service, CliSessionService):
        session_data = await cli_session_service.get_active_session()
        if session_data:
            # Return as JSON dict instead of CliSession object
            return {
                "execution_id": session_data.execution_id,
                "diagram_name": session_data.diagram_name,
                "diagram_format": session_data.diagram_format,
                "started_at": session_data.started_at.isoformat()
                if session_data.started_at
                else None,
                "is_active": session_data.is_active,
                "diagram_data": session_data.diagram_data,
                "node_states": session_data.node_states,
                "session_id": f"cli_{session_data.execution_id}",  # Include computed field
            }

    return {}
