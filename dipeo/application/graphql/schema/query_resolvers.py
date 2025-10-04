"""Standalone query resolver functions for use with OperationExecutor.

These resolvers are extracted from the Query class to support the operation-based architecture.
Each resolver function takes a ServiceRegistry as its first parameter.
"""

import logging
from datetime import datetime
from pathlib import Path

import strawberry
from strawberry.scalars import JSON

from dipeo.application.graphql.graphql_types.provider_types import (
    OperationSchemaType,
    OperationType,
    ProviderStatisticsType,
    ProviderType,
)
from dipeo.application.graphql.resolvers.provider_resolver import ProviderResolver
from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import (
    API_KEY_SERVICE,
    CLI_SESSION_SERVICE,
    DIAGRAM_PORT,
    EXECUTION_ORCHESTRATOR,
    FILESYSTEM_ADAPTER,
    STATE_STORE,
)
from dipeo.config import FILES_DIR
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import LLMService, NodeType
from dipeo.diagram_generated.domain_models import ApiKeyID, DiagramID, ExecutionID, PersonID
from dipeo.diagram_generated.graphql.domain_types import (
    DomainApiKeyType,
    DomainDiagramType,
    DomainPersonType,
    ExecutionStateType,
)
from dipeo.diagram_generated.graphql.inputs import DiagramFilterInput, ExecutionFilterInput

logger = get_module_logger(__name__)
DIAGRAM_VERSION = "1.0.0"


# Query resolvers - Diagrams
async def get_diagram(
    registry: ServiceRegistry, diagram_id: strawberry.ID
) -> DomainDiagramType | None:
    """Get a single diagram by ID."""
    try:
        service = registry.resolve(DIAGRAM_PORT)
        diagram_id_typed = DiagramID(str(diagram_id))
        diagram_data = await service.get_diagram(diagram_id_typed)
        return diagram_data
    except FileNotFoundError:
        logger.warning(f"Diagram not found: {diagram_id}")
        return None
    except Exception as e:
        logger.error(f"Error fetching diagram {diagram_id}: {e}")
        raise


async def list_diagrams(
    registry: ServiceRegistry,
    filter: DiagramFilterInput | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[DomainDiagramType]:
    """List diagrams with optional filtering."""
    try:
        service = registry.resolve(DIAGRAM_PORT)
        all_infos = await service.list_diagrams()
        logger.debug(f"Retrieved {len(all_infos)} diagram infos")

        filtered_infos = all_infos
        if filter:
            filtered_infos = [info for info in all_infos if _matches_diagram_filter(info, filter)]

        paginated_infos = filtered_infos[offset : offset + limit]
        diagrams = []
        for info in paginated_infos:
            try:
                diagram = await service.get_diagram(info.id)
                if diagram:
                    diagrams.append(diagram)
            except Exception as e:
                logger.warning(f"Failed to load diagram {info.id}: {e}")
                from dipeo.diagram_generated import DiagramMetadata, DomainDiagram

                name = None
                if info.metadata and "name" in info.metadata:
                    name = info.metadata["name"]
                elif info.path:
                    name = Path(info.path).stem

                now_str = datetime.now().isoformat()

                try:
                    minimal_diagram = DomainDiagram(
                        nodes=[],
                        arrows=[],
                        handles=[],
                        persons=[],
                        metadata=DiagramMetadata(
                            id=info.id,
                            name=name or info.id,
                            description=f"Failed to load: {str(e)[:100]}",
                            version="1.0",
                            created=str(info.created) if info.created else now_str,
                            modified=str(info.modified) if info.modified else now_str,
                        ),
                    )
                    diagrams.append(minimal_diagram)
                except Exception as fallback_error:
                    logger.error(
                        f"Failed to create minimal diagram for {info.id}: {fallback_error}"
                    )
                    continue

        return diagrams

    except Exception as e:
        import traceback

        logger.error(f"Error listing diagrams: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


def _matches_diagram_filter(info, filter: DiagramFilterInput) -> bool:
    """Helper function to check if a DiagramInfo matches the filter criteria."""
    name = ""
    if info.metadata and "name" in info.metadata:
        name = info.metadata["name"]
    elif info.path:
        name = info.path.stem

    if filter.name and filter.name.lower() not in name.lower():
        return False

    if filter.author:
        author = info.metadata.get("author", "") if info.metadata else ""
        if filter.author != author:
            return False

    if filter.tags:
        tags = info.metadata.get("tags", []) if info.metadata else []
        if not any(tag in tags for tag in filter.tags):
            return False

    return True


# Query resolvers - Executions
async def get_execution(
    registry: ServiceRegistry, execution_id: strawberry.ID
) -> ExecutionStateType | None:
    """Get a single execution by ID."""
    try:
        state_store = registry.resolve(STATE_STORE)
        execution_id_typed = ExecutionID(str(execution_id))
        execution = await state_store.get_state(str(execution_id_typed))

        if not execution:
            return None

        return ExecutionStateType.from_pydantic(execution)

    except Exception as e:
        logger.error(f"Error fetching execution {execution_id}: {e}")
        return None


async def list_executions(
    registry: ServiceRegistry,
    filter: ExecutionFilterInput | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ExecutionStateType]:
    """List executions with optional filtering."""
    try:
        state_store = registry.resolve(STATE_STORE)
        executions = await state_store.list_executions(
            diagram_id=filter.diagram_id if filter else None,
            status=filter.status if filter else None,
            limit=limit,
            offset=offset,
        )

        return [ExecutionStateType.from_pydantic(state) for state in executions]

    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        return []


async def get_execution_order(registry: ServiceRegistry, execution_id: strawberry.ID) -> JSON:
    """Get the execution order for a given execution."""
    state_store = registry.resolve(STATE_STORE)
    execution_id_typed = ExecutionID(str(execution_id))
    execution = await state_store.get_state(str(execution_id_typed))

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
                "status": node_state.status.name if hasattr(node_state, "status") else "UNKNOWN",
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
        "status": execution.status.name if hasattr(execution, "status") else "UNKNOWN",
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

    state_store = registry.resolve(STATE_STORE)
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

    execution = await state_store.get_state(str(execution_id_typed))
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
    try:
        state_store = registry.resolve(STATE_STORE)
        filter_input = None
        if diagram_id:
            filter_input = ExecutionFilterInput(diagram_id=DiagramID(str(diagram_id)))

        executions = await state_store.list_executions(
            diagram_id=filter_input.diagram_id if filter_input else None,
            status=filter_input.status if filter_input else None,
            limit=limit,
            offset=0,
        )

        if not include_metrics:
            for execution in executions:
                if hasattr(execution, "metrics"):
                    execution.metrics = None

        return [ExecutionStateType.from_pydantic(execution) for execution in executions]

    except Exception as e:
        logger.error(f"Error getting execution history: {e}")
        return []


# Query resolvers - Persons
async def get_person(
    registry: ServiceRegistry, person_id: strawberry.ID
) -> DomainPersonType | None:
    """Get a single person by ID."""
    try:
        from dipeo.diagram_generated.domain_models import PersonLLMConfig

        integrated_service = registry.resolve(DIAGRAM_PORT)
        if not integrated_service:
            logger.warning("Integrated diagram service not available")
            return None

        diagram_infos = await integrated_service.list_diagrams()
        person_id_typed = PersonID(str(person_id))

        for diagram_info in diagram_infos:
            path = diagram_info.get("path", "")
            diagram_id = path.split(".")[0] if path else diagram_info.get("id")

            diagram_dict = await integrated_service.get_diagram(diagram_id)
            if not diagram_dict:
                continue

            persons = diagram_dict.get("persons", {})
            if str(person_id_typed) in persons:
                person_data = persons[str(person_id_typed)]
                return DomainPersonType(
                    id=person_id_typed,
                    label=person_data.get("name", ""),
                    llm_config=PersonLLMConfig(
                        service=person_data.get("service", "openai"),
                        model=person_data.get("modelName", "gpt-4.1-nano"),
                        api_key_id=person_data.get("apiKeyId", ""),
                        system_prompt=person_data.get("systemPrompt", ""),
                    ),
                    type="person",
                )

        return None

    except Exception as e:
        logger.error(f"Error fetching person {person_id}: {e}")
        return None


async def list_persons(registry: ServiceRegistry, limit: int = 100) -> list[DomainPersonType]:
    """List all persons."""
    try:
        from dipeo.diagram_generated.domain_models import PersonLLMConfig

        integrated_service = registry.resolve(DIAGRAM_PORT)
        if not integrated_service:
            logger.warning("Integrated diagram service not available")
            return []

        all_persons = {}
        diagram_infos = await integrated_service.list_diagrams()

        for diagram_info in diagram_infos:
            path = diagram_info.get("path", "")
            diagram_id = path.split(".")[0] if path else diagram_info.get("id")

            diagram_dict = await integrated_service.get_diagram(diagram_id)
            if not diagram_dict:
                continue

            persons = diagram_dict.get("persons", {})
            for person_id, person_data in persons.items():
                if person_id not in all_persons:
                    all_persons[person_id] = DomainPersonType(
                        id=PersonID(person_id),
                        label=person_data.get("name", ""),
                        llm_config=PersonLLMConfig(
                            service=person_data.get("service", "openai"),
                            model=person_data.get("modelName", "gpt-4.1-nano"),
                            api_key_id=person_data.get("apiKeyId", ""),
                            system_prompt=person_data.get("systemPrompt", ""),
                        ),
                        type="person",
                    )

        domain_persons = list(all_persons.values())
        return domain_persons[:limit]

    except Exception as e:
        logger.error(f"Error listing persons: {e}")
        return []


# Query resolvers - API Keys
async def get_api_key(
    registry: ServiceRegistry, api_key_id: strawberry.ID
) -> DomainApiKeyType | None:
    """Get a single API key by ID."""
    try:
        import asyncio

        apikey_service = registry.resolve(API_KEY_SERVICE)
        api_keys = await asyncio.to_thread(apikey_service.list_api_keys)
        api_key_id_typed = ApiKeyID(str(api_key_id))

        for key_data in api_keys:
            if key_data.get("id") == str(api_key_id_typed):
                return DomainApiKeyType(
                    id=key_data["id"],
                    label=key_data["label"],
                    service=key_data["service"],
                    key=key_data.get("key", "***hidden***"),
                )

        return None

    except Exception as e:
        logger.error(f"Error fetching API key {api_key_id}: {e}")
        return None


async def get_api_keys(
    registry: ServiceRegistry, service: str | None = None
) -> list[DomainApiKeyType]:
    """List API keys, optionally filtered by service."""
    try:
        import asyncio

        from dipeo.diagram_generated.enums import APIServiceType

        valid_services = {s.value for s in APIServiceType}

        apikey_service = registry.resolve(API_KEY_SERVICE)
        logger.debug(f"Got apikey_service: {apikey_service}")
        api_keys = await asyncio.to_thread(apikey_service.list_api_keys)
        logger.debug(f"Got {len(api_keys)} API keys from service")

        domain_keys = []
        for key_data in api_keys:
            if key_data.get("service") not in valid_services:
                logger.debug(f"Skipping non-LLM service: {key_data.get('service')}")
                continue

            if service and key_data.get("service") != service:
                continue

            domain_keys.append(
                DomainApiKeyType(
                    id=key_data["id"],
                    label=key_data["label"],
                    service=key_data["service"],
                    key=key_data.get("key", "***hidden***"),
                )
            )

        return domain_keys

    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        return []


async def get_available_models(
    registry: ServiceRegistry, service: str, api_key_id: strawberry.ID
) -> list[str]:
    """Get available models for a given service and API key."""
    try:
        api_key_id_typed = ApiKeyID(str(api_key_id))
        api_key = await get_api_key(registry, api_key_id)
        if not api_key:
            logger.warning(f"API key not found: {api_key_id}")
            return []

        from dipeo.application.registry.keys import LLM_SERVICE

        llm_service = registry.resolve(LLM_SERVICE)
        models = await llm_service.get_available_models(api_key_id_typed)

        return models

    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        return []


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


# Note: get_supported_formats removed as DIAGRAM_CONVERTER service was unused
# If needed in future, implement using DIAGRAM_SERIALIZER or other appropriate service


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
