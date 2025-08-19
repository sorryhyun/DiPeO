"""Minimal wiring for thin startup - only registers services actually used at runtime."""

from typing import Optional
from dipeo.application.registry import ServiceRegistry


def wire_minimal(registry: ServiceRegistry, redis_client: Optional[object] = None) -> None:
    """Wire only the minimal set of services actually used at runtime.
    
    This avoids registering ~37 unused services identified by runtime analysis.
    Services are wired lazily on first use where possible.
    
    Args:
        registry: The service registry to wire services into
        redis_client: Optional Redis client for distributed state
    """
    from dipeo.application.bootstrap.wiring import (
        wire_state_services,
        wire_event_services,
    )
    from dipeo.application.diagram.wiring import (
        wire_diagram_port,
        wire_diagram_use_cases,
    )
    from dipeo.application.execution.wiring import wire_execution
    from dipeo.application.conversation.wiring import wire_conversation
    
    # Core services that are always needed
    wire_state_services(registry, redis_client)
    wire_event_services(registry)
    
    # Diagram services - only the essentials
    wire_diagram_port(registry)
    wire_diagram_use_cases(registry)
    
    # Execution services - orchestrator and use cases only
    wire_execution(registry)
    
    # Conversation services - only if actually used
    # Check if PersonJob nodes exist in the diagram before wiring
    # This can be determined at runtime based on diagram content
    wire_conversation(registry)
    
    # Note: The following services are NOT wired by default as they're unused:
    # - API_PROVIDER_REGISTRY
    # - API_SERVICE (replaced by specific services)
    # - ARTIFACT_STORE
    # - AST_PARSER (only needed for TypeScript AST node)
    # - BLOB_STORAGE / BLOB_STORE (duplicates)
    # - CLI_SESSION_USE_CASE (wired separately in server context)
    # - COMPILE_DIAGRAM_USE_CASE (not used directly)
    # - COMPILE_TIME_RESOLVER (internal to compilation)
    # - DIAGRAM_RESOLVER_KEY (internal)
    # - EXECUTE_DIAGRAM_USE_CASE (not used directly)
    # - EXECUTION_ORCHESTRATOR (not resolved directly)
    
    # These can be wired on-demand if specific node types require them


def wire_feature_flags(registry: ServiceRegistry, features: list[str]) -> None:
    """Wire optional features based on feature flags.
    
    Args:
        registry: The service registry
        features: List of feature names to enable
    """
    if "ast_parser" in features:
        from dipeo.application.bootstrap.infrastructure_container import wire_ast_parser
        wire_ast_parser(registry)
    
    if "blob_storage" in features:
        from dipeo.application.bootstrap.wiring import wire_blob_storage
        wire_blob_storage(registry)
    
    if "artifact_store" in features:
        from dipeo.application.bootstrap.infrastructure_container import wire_artifact_store
        wire_artifact_store(registry)
    
    # Add more feature flags as needed