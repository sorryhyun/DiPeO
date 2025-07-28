"""GraphQL queries for DiPeO API."""

from datetime import datetime

import strawberry
from dipeo.core.constants import FILES_DIR
from dipeo.models import LLMService, NodeType

from dipeo_server.shared.constants import DIAGRAM_VERSION

from .types_new import (
    ApiKeyID,
    DiagramFilterInput,
    DiagramFormatInfo,
    DiagramID,
    DomainApiKeyType,
    DomainDiagramType,
    DomainPersonType,
    ExecutionFilterInput,
    ExecutionID,
    ExecutionStateType,
    JSONScalar,
    PersonID,
)


@strawberry.type
class Query:
    @strawberry.field
    async def diagram(self, id: DiagramID, info) -> DomainDiagramType | None:
        from .resolvers.diagram import diagram_resolver

        return await diagram_resolver.get_diagram(id, info)

    @strawberry.field
    async def diagrams(
        self,
        info,
        filter: DiagramFilterInput | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DomainDiagramType]:
        from .resolvers.diagram import diagram_resolver

        return await diagram_resolver.list_diagrams(filter, limit, offset, info)

    @strawberry.field
    async def execution(self, id: ExecutionID, info) -> ExecutionStateType | None:
        from .resolvers.execution import execution_resolver

        return await execution_resolver.get_execution(id, info)

    @strawberry.field
    async def executions(
        self,
        info,
        filter: ExecutionFilterInput | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionStateType]:
        from .resolvers.execution import execution_resolver

        return await execution_resolver.list_executions(filter, limit, offset, info)

    @strawberry.field
    async def person(self, id: PersonID, info) -> DomainPersonType | None:
        from .resolvers.person import person_resolver

        return await person_resolver.get_person(id, info)

    @strawberry.field
    async def persons(self, info, limit: int = 100) -> list[DomainPersonType]:
        from .resolvers.person import person_resolver

        return await person_resolver.list_persons(limit, info)

    @strawberry.field
    async def api_key(self, id: ApiKeyID, info) -> DomainApiKeyType | None:
        from .resolvers.person import person_resolver

        return await person_resolver.get_api_key(id, info)

    @strawberry.field
    async def api_keys(
        self, info, service: str | None = None
    ) -> list[DomainApiKeyType]:
        from .resolvers.person import person_resolver

        return await person_resolver.list_api_keys(service, info)

    @strawberry.field
    async def available_models(
        self, service: str, api_key_id: ApiKeyID, info
    ) -> list[str]:
        from .resolvers.person import person_resolver

        return await person_resolver.get_available_models(service, api_key_id, info)

    @strawberry.field
    async def system_info(self, info) -> JSONScalar:
        return {
            "version": DIAGRAM_VERSION,
            "supported_node_types": [t.value for t in NodeType],
            "supported_llm_services": [s.value for s in LLMService],
            "max_upload_size_mb": 100,
            "graphql_subscriptions_enabled": True,
        }

    @strawberry.field
    async def execution_capabilities(self, info) -> JSONScalar:
        context = info.context

        integrated_service = context.get_service("integrated_diagram_service")
        persons_list = []

        diagram_infos = await integrated_service.list_diagrams()
        for diagram_info in diagram_infos:
            # Extract diagram ID from path
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
    async def health(self, info) -> JSONScalar:
        context = info.context

        checks = {"database": False, "redis": False, "file_system": False}

        try:
            await context.get_service("state_store").list_executions(limit=1)
            checks["database"] = True
        except:
            pass

        checks["redis"] = False

        try:
            (FILES_DIR / "diagrams").exists()
            checks["file_system"] = True
        except:
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
        info,
        person_id: PersonID | None = None,
        execution_id: ExecutionID | None = None,
        search: str | None = None,
        show_forgotten: bool = False,
        limit: int = 100,
        offset: int = 0,
        since: datetime | None = None,
    ) -> JSONScalar:
        context = info.context
        conversation_service = context.get_service("conversation_service")

        all_conversations = []

        if (
            not hasattr(conversation_service, "person_conversations")
            or not conversation_service.person_conversations
        ):
            return {
                "conversations": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
            }

        for (
            person_id_key,
            person_conversation,
        ) in conversation_service.person_conversations.items():
            if person_id and person_id_key != person_id:
                continue

            for message in person_conversation.messages:
                is_forgotten = message.id in person_conversation.forgotten_message_ids
                if not show_forgotten and is_forgotten:
                    continue

                if execution_id and message.execution_id != execution_id:
                    continue

                if search:
                    search_lower = search.lower()
                    if not any(
                        search_lower in str(v).lower()
                        for v in [
                            message.content,
                            message.node_label or "",
                            message.node_id or "",
                        ]
                    ):
                        continue

                if since and message.timestamp < since:
                    continue

                conversation = {
                    "id": message.id,
                    "personId": person_id_key,
                    "executionId": message.execution_id,
                    "nodeId": message.node_id,
                    "nodeLabel": message.node_label,
                    "timestamp": message.timestamp.isoformat(),
                    "userPrompt": "",  # Not stored separately in new system
                    "assistantResponse": message.content,
                    "forgotten": is_forgotten,
                    "tokenUsage": {
                        "total": message.token_count or 0,
                        "input": message.input_tokens or 0,
                        "output": message.output_tokens or 0,
                        "cached": message.cached_tokens or 0,
                    }
                    if message.token_count
                    else None,
                }
                all_conversations.append(conversation)

        all_conversations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        paginated = all_conversations[offset : offset + limit]

        return {
            "conversations": paginated,
            "total": len(all_conversations),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(all_conversations),
        }

    @strawberry.field
    async def supported_formats(self, info) -> list[DiagramFormatInfo]:
        from dipeo.infra.diagram import converter_registry

        formats = converter_registry.list_formats()
        return [
            DiagramFormatInfo(
                id=fmt["id"],
                name=fmt["name"],
                description=fmt["description"],
                extension=fmt["extension"],
                supports_import=fmt.get("supports_import", True),
                supports_export=fmt.get("supports_export", True),
            )
            for fmt in formats
        ]

    @strawberry.field
    async def execution_order(self, execution_id: ExecutionID, info) -> JSONScalar:
        from .resolvers.diagram import diagram_resolver
        from .resolvers.execution import execution_resolver

        execution = await execution_resolver.get_execution(execution_id, info)
        if not execution:
            return {
                "executionId": execution_id,
                "nodes": [],
                "error": "Execution not found",
            }

        # Create a mapping of node_id to node_name from the diagram
        node_names = {}
        diagram_id = (
            getattr(execution._pydantic_object, "diagram_id", None)
            if hasattr(execution, "_pydantic_object")
            else None
        )
        if diagram_id:
            diagram = await diagram_resolver.get_diagram(diagram_id, info)
            if (
                diagram
                and hasattr(diagram, "_pydantic_object")
                and diagram._pydantic_object.nodes
            ):
                for node in diagram._pydantic_object.nodes:
                    # Use display_name if available, otherwise try data.label, fallback to node.id
                    if node.display_name:
                        node_names[node.id] = node.display_name
                    elif (
                        hasattr(node, "data")
                        and isinstance(node.data, dict)
                        and "label" in node.data
                    ):
                        node_names[node.id] = node.data["label"]
                    else:
                        node_names[node.id] = node.id

        # Extract node execution order from node_states
        node_order = []
        if (
            hasattr(execution, "_pydantic_object")
            and execution._pydantic_object.node_states
        ):
            node_states_dict = execution._pydantic_object.node_states
            for node_id, node_state in node_states_dict.items():
                # Handle if node_state is a pydantic model
                if hasattr(node_state, "model_dump"):
                    node_state = node_state.model_dump()
                elif not isinstance(node_state, dict):
                    continue

                if node_state.get("startedAt"):
                    node_info = {
                        "nodeId": node_id,
                        "nodeName": node_names.get(
                            node_id, node_id
                        ),  # Use actual node name from diagram
                        "status": node_state.get("status", "PENDING"),
                        "startedAt": node_state.get("startedAt"),
                        "endedAt": node_state.get("endedAt"),
                        "error": node_state.get("error"),
                        "tokenUsage": node_state.get("tokenUsage"),
                    }

                    # Calculate duration if both timestamps exist
                    if node_info["startedAt"] and node_info["endedAt"]:
                        start = datetime.fromisoformat(
                            node_info["startedAt"].replace("Z", "+00:00")
                        )
                        end = datetime.fromisoformat(
                            node_info["endedAt"].replace("Z", "+00:00")
                        )
                        duration = (
                            end - start
                        ).total_seconds() * 1000  # Convert to milliseconds
                        node_info["duration"] = int(duration)

                    node_order.append(node_info)

        # Sort by startedAt timestamp
        node_order.sort(key=lambda x: x.get("startedAt", ""))

        return {
            "executionId": execution_id,
            "status": execution._pydantic_object.status
            if hasattr(execution, "_pydantic_object")
            else None,
            "startedAt": execution._pydantic_object.started_at
            if hasattr(execution, "_pydantic_object")
            else None,
            "endedAt": execution._pydantic_object.ended_at
            if hasattr(execution, "_pydantic_object")
            else None,
            "nodes": node_order,
            "totalNodes": len(node_order),
        }

    @strawberry.field
    async def prompt_files(self, info) -> list[JSONScalar]:
        context = info.context
        file_service = context.get_service("file_service")
        return await file_service.list_prompt_files()

    @strawberry.field
    async def prompt_file(self, filename: str, info) -> JSONScalar:
        context = info.context
        file_service = context.get_service("file_service")
        return await file_service.read_prompt_file(filename)
