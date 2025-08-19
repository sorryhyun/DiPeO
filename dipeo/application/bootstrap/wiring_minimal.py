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
    
    # Note: The following services have been REMOVED from the codebase:
    # - API_PROVIDER_REGISTRY (never used, webhooks use PROVIDER_REGISTRY)
    # - API_SERVICE (replaced by specific services)
    # - ARTIFACT_STORE (no handlers use this)
    # - COMPILE_TIME_RESOLVER (internal to compilation)
    # - FILE_SYSTEM (removed duplicate, use FILESYSTEM_ADAPTER)
    # - BLOB_STORAGE (removed duplicate, use BLOB_STORE)
    # - CONVERSATION_SERVICE (removed duplicate, use CONVERSATION_MANAGER)
    # - DIAGRAM_SERVICE (removed duplicate, use DIAGRAM_PORT)
    #
    # The following services are NOT wired by default but can be enabled:
    # - AST_PARSER (only needed for TypeScript AST node)
    # - Port metrics (set DIPEO_PORT_METRICS=1 to enable)
    
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
        from dipeo.application.bootstrap.wiring import wire_storage_services
        wire_storage_services(registry)
    
    # Add more feature flags as needed