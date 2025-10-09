"""Helper functions for diagram preparation."""

import logging
import re
from typing import TYPE_CHECKING

from dipeo.config.base_logger import get_module_logger

if TYPE_CHECKING:
    from dipeo.diagram_generated import DomainDiagram
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
    from dipeo.infrastructure.security.keys import APIKeyService

logger = get_module_logger(__name__)


def extract_api_keys_from_domain(
    diagram: "DomainDiagram", api_key_service: "APIKeyService"
) -> dict[str, str]:
    """Extract API keys needed for execution from DomainDiagram.

    Args:
        diagram: Domain diagram to extract API keys from
        api_key_service: API key service for retrieving keys

    Returns:
        Dictionary mapping API key IDs to actual keys
    """
    keys = {}

    # Get all available API keys
    all_keys = {
        info["id"]: api_key_service.get_api_key(info["id"])["key"]
        for info in api_key_service.list_api_keys()
    }

    # Extract API keys from persons
    if hasattr(diagram, "persons") and diagram.persons:
        # Handle both dict and list formats
        persons_list = (
            list(diagram.persons.values()) if isinstance(diagram.persons, dict) else diagram.persons
        )
        for person in persons_list:
            # Get api_key_id from llm_config
            if hasattr(person, "llm_config") and hasattr(person.llm_config, "api_key_id"):
                api_key_id = str(person.llm_config.api_key_id)

                # Add the API key to the keys dict if it exists
                if api_key_id in all_keys:
                    keys[api_key_id] = all_keys[api_key_id]
                else:
                    logger.warning(f"API key {api_key_id} not found in available keys")

    return keys


async def register_todo_diagram_if_needed(
    todo_sync_service,
    domain_diagram: "DomainDiagram",
    executable_diagram: "ExecutableDiagram",
) -> None:
    """Check if this is a TODO-backed diagram and register it with TodoSyncService.

    Args:
        todo_sync_service: TODO sync service for registration
        domain_diagram: The domain diagram
        executable_diagram: The executable diagram
    """
    if not todo_sync_service:
        return

    # Check if this diagram has TODO metadata
    if not domain_diagram.metadata:
        return

    metadata_dict = (
        domain_diagram.metadata.model_dump()
        if hasattr(domain_diagram.metadata, "model_dump")
        else domain_diagram.metadata
    )

    # Look for TODO source indicators in metadata
    is_todo_diagram = False
    session_id = None
    trace_id = None

    # Check for claude_code_todo source
    if metadata_dict.get("source") == "claude_code_todo":
        is_todo_diagram = True
        session_id = metadata_dict.get("session_id")
        trace_id = metadata_dict.get("trace_id")

    # Check for TODO-related paths
    diagram_path = executable_diagram.metadata.get("diagram_source_path", "")
    if "dipeo_cc" in diagram_path or "todo_" in diagram_path:
        is_todo_diagram = True
        # Extract session ID from path if not already set
        if not session_id and "todo_" in diagram_path:
            # Try to extract session ID from filename pattern: todo_<session_id>_<timestamp>
            match = re.search(r"todo_([^_/]+)_", diagram_path)
            if match:
                session_id = match.group(1)

    if is_todo_diagram and session_id:
        try:
            # Register the session with TodoSyncService
            await todo_sync_service.register_session(session_id, trace_id)

            # Store sync metadata in executable diagram
            executable_diagram.metadata["todo_sync"] = {
                "enabled": True,
                "session_id": session_id,
                "trace_id": trace_id,
                "source": "claude_code_todo",
            }

            logger.info(
                f"[PrepareDiagramForExecution] Registered TODO diagram for session {session_id}"
            )
        except Exception as e:
            logger.warning(f"[PrepareDiagramForExecution] Failed to register TODO diagram: {e}")
