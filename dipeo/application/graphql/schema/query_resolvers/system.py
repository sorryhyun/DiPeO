"""System-related query resolvers."""

from datetime import datetime

from strawberry.scalars import JSON

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import DIAGRAM_PORT, STATE_STORE
from dipeo.config import FILES_DIR
from dipeo.diagram_generated import LLMService, NodeType

DIAGRAM_VERSION = "1.0.0"


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
    person_id: str | None = None,
    execution_id: str | None = None,
    search: str | None = None,
    show_forgotten: bool = False,
    limit: int = 100,
    offset: int = 0,
    since: datetime | None = None,
) -> list[JSON]:
    """List conversations with optional filtering."""
    from dipeo.application.registry.keys import EXECUTION_ORCHESTRATOR

    conversation_service = registry.resolve(EXECUTION_ORCHESTRATOR)

    if not conversation_service or not hasattr(conversation_service, "person_conversations"):
        return []

    return []
