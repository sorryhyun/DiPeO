"""Diagram preparation for execution."""

import contextlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dipeo.application.registry import ServiceRegistry
    from dipeo.diagram_generated import DomainDiagram
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram


async def prepare_and_compile_diagram(
    service_registry: "ServiceRegistry",
    diagram: "DomainDiagram",
    options: dict[str, Any],
) -> "ExecutableDiagram":
    """Prepare and compile diagram using the standard flow.

    Args:
        service_registry: Service registry
        diagram: Domain diagram to prepare
        options: Execution options

    Returns:
        Compiled executable diagram
    """
    from dipeo.application.registry import PREPARE_DIAGRAM_USE_CASE

    # Try to get prepare diagram service from registry
    prepare_diagram_service = None
    with contextlib.suppress(Exception):
        prepare_diagram_service = service_registry.resolve(PREPARE_DIAGRAM_USE_CASE)

    # If we have the prepare service, use it for clean deserialization -> compilation
    if prepare_diagram_service:
        # Prepare diagram handles all format conversion and compilation
        # Pass diagram_source_path from options if available
        diagram_id = options.get("diagram_source_path")
        executable_diagram = await prepare_diagram_service.prepare_for_execution(
            diagram=diagram,
            diagram_id=diagram_id,  # Pass the original source path
            validate=False,  # Skip validation for now as mentioned in TODO
        )
    else:
        # Fallback to inline implementation if service not available
        executable_diagram = await _fallback_prepare_and_compile(service_registry, diagram, options)

    await register_person_configs(service_registry, executable_diagram)

    return executable_diagram


async def _fallback_prepare_and_compile(
    service_registry: "ServiceRegistry",
    diagram: "DomainDiagram",
    options: dict[str, Any],
) -> "ExecutableDiagram":
    """Fallback diagram compilation when prepare service is not available."""
    from dipeo.application.registry import API_KEY_SERVICE
    from dipeo.application.registry.keys import DIAGRAM_COMPILER

    # Already have a DomainDiagram, just compile it
    domain_diagram = diagram

    # Compile to ExecutableDiagram
    compiler = service_registry.resolve(DIAGRAM_COMPILER)
    if not compiler:
        raise RuntimeError("DiagramCompiler not found in registry")

    executable_diagram = compiler.compile(domain_diagram)

    # Add API keys
    api_key_service = service_registry.resolve(API_KEY_SERVICE)
    if api_key_service:
        api_keys = extract_api_keys_for_diagram(domain_diagram, api_key_service)
        if api_keys:
            executable_diagram.metadata["api_keys"] = api_keys

    # Add metadata
    if domain_diagram.metadata:
        executable_diagram.metadata.update(domain_diagram.metadata.__dict__)

    # Add diagram source path if available
    diagram_source_path = options.get("diagram_source_path")
    if diagram_source_path:
        executable_diagram.metadata["diagram_source_path"] = diagram_source_path
        # Also set as diagram_id if not already set
        if "diagram_id" not in executable_diagram.metadata:
            executable_diagram.metadata["diagram_id"] = diagram_source_path

    # Add persons metadata
    if hasattr(domain_diagram, "persons") and domain_diagram.persons:
        persons_dict = {}
        persons_list = (
            list(domain_diagram.persons.values())
            if isinstance(domain_diagram.persons, dict)
            else domain_diagram.persons
        )
        for person in persons_list:
            person_id = str(person.id)
            persons_dict[person_id] = {
                "name": person.label,
                "service": person.llm_config.service.value
                if hasattr(person.llm_config.service, "value")
                else person.llm_config.service,
                "model": person.llm_config.model,
                "api_key_id": str(person.llm_config.api_key_id),
                "system_prompt": person.llm_config.system_prompt or "",
                "temperature": getattr(person.llm_config, "temperature", 0.7),
                "max_tokens": getattr(person.llm_config, "max_tokens", None),
            }
        executable_diagram.metadata["persons"] = persons_dict

    return executable_diagram


async def register_person_configs(
    service_registry: "ServiceRegistry",
    diagram: "ExecutableDiagram",
) -> None:
    """Register person configurations from typed diagram.

    Args:
        service_registry: Service registry
        diagram: Executable diagram with person metadata
    """
    from dipeo.application.registry import EXECUTION_ORCHESTRATOR
    from dipeo.diagram_generated.generated_nodes import NodeType, PersonJobNode

    conversation_service = None
    if hasattr(service_registry, "resolve"):
        # Use the consolidated conversation manager service
        conversation_service = service_registry.resolve(EXECUTION_ORCHESTRATOR)

    if conversation_service:
        # Register persons from typed nodes
        person_job_nodes = diagram.get_nodes_by_type(NodeType.PERSON_JOB)
        for node in person_job_nodes:
            if isinstance(node, PersonJobNode) and node.person:
                person_id = str(node.person)

                # Get person config from metadata if available, otherwise empty dict
                person_config = {}
                if diagram.metadata and "persons" in diagram.metadata:
                    persons_metadata = diagram.metadata["persons"]
                    if person_id in persons_metadata:
                        person_config = persons_metadata[person_id]

                # Register person - repository will handle defaults
                if hasattr(conversation_service, "register_person"):
                    conversation_service.register_person(person_id, person_config)
                else:
                    # For services that don't have register_person,
                    # we can at least ensure the person memory is created
                    if hasattr(conversation_service, "get_or_create_person_memory"):
                        conversation_service.get_or_create_person_memory(person_id)


def extract_api_keys_for_diagram(diagram: "DomainDiagram", api_key_service) -> dict[str, str]:
    """Extract API keys needed by the diagram.

    Args:
        diagram: The domain diagram (before compilation)
        api_key_service: The API key service

    Returns:
        Dictionary mapping API key IDs to actual keys
    """
    api_keys = {}

    # Get all available API keys
    all_keys = {
        info["id"]: api_key_service.get_api_key(info["id"])["key"]
        for info in api_key_service.list_api_keys()
    }

    # Extract API key references from persons
    if hasattr(diagram, "persons") and diagram.persons:
        # Handle both dict and list formats
        persons_list = (
            list(diagram.persons.values()) if isinstance(diagram.persons, dict) else diagram.persons
        )
        for person in persons_list:
            api_key_id = None
            if hasattr(person, "api_key_id"):
                api_key_id = person.api_key_id
            if api_key_id and api_key_id in all_keys:
                api_keys[api_key_id] = all_keys[api_key_id]

    return api_keys
