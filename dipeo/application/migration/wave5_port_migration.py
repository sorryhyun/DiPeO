"""Wave 5 Migration: Update all call sites to use domain ports instead of core/ports.

This module provides mappings and utilities for migrating from old core/ports
to new domain ports with backward compatibility via feature flags.
"""

import logging
from typing import Any, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Port migration mappings
PORT_MIGRATIONS = {
    # State management
    "dipeo.core.ports.StateStorePort": {
        "new_module": "dipeo.domain.execution.state.ports",
        "new_name": "ExecutionStateRepository",
        "registry_token": "STATE_REPOSITORY",
        "feature_flag": "STATE_PORT_V2",
    },
    "dipeo.core.ports.StateServicePort": {
        "new_module": "dipeo.domain.execution.state.ports",
        "new_name": "ExecutionStateService",
        "registry_token": "STATE_SERVICE",
        "feature_flag": "STATE_PORT_V2",
    },
    
    # Messaging
    "dipeo.core.ports.MessageRouterPort": {
        "new_module": "dipeo.domain.messaging.ports",
        "new_name": "MessageBus",
        "registry_token": "MESSAGE_BUS",
        "feature_flag": "MESSAGING_PORT_V2",
    },
    
    # LLM Services
    "dipeo.core.ports.LLMServicePort": {
        "new_module": "dipeo.domain.llm.ports",
        "new_name": "LLMService",
        "registry_token": "LLM_SERVICE",
        "feature_flag": "LLM_PORT_V2",
    },
    "dipeo.core.ports.LLMClientPort": {
        "new_module": "dipeo.domain.llm.ports",
        "new_name": "LLMClient",
        "registry_token": "LLM_CLIENT",
        "feature_flag": "LLM_PORT_V2",
    },
    
    # API Integration
    "dipeo.core.ports.IntegratedApiServicePort": {
        "new_module": "dipeo.domain.integrations.ports",
        "new_name": "ApiInvoker",
        "registry_token": "API_INVOKER",
        "feature_flag": "API_PORT_V2",
    },
    "dipeo.core.ports.ApiProviderPort": {
        "new_module": "dipeo.domain.integrations.ports",
        "new_name": "ApiProvider",
        "registry_token": "API_PROVIDER",
        "feature_flag": "API_PORT_V2",
    },
    
    # Storage
    "dipeo.core.ports.FileServicePort": {
        "new_module": "dipeo.domain.storage.ports",
        "new_name": "StoragePort",
        "registry_token": "STORAGE_SERVICE",
        "feature_flag": "STORAGE_PORT_V2",
    },
    
    # Events
    "dipeo.core.ports.ExecutionObserver": {
        "new_module": "dipeo.domain.events.ports",
        "new_name": "DomainEventBus",
        "registry_token": "DOMAIN_EVENT_BUS",
        "feature_flag": "EVENTS_PORT_V2",
        "adapter": "ObserverToEventAdapter",
    },
}


def get_port_import(old_import: str, use_v2: bool = False) -> tuple[str, str]:
    """Get the appropriate import path based on feature flag.
    
    Args:
        old_import: The old core.ports import path
        use_v2: Whether to use V2 domain ports
        
    Returns:
        Tuple of (module_path, class_name)
    """
    if not use_v2:
        # Use old core port
        parts = old_import.rsplit(".", 1)
        return parts[0], parts[1] if len(parts) > 1 else ""
    
    # Look up migration mapping
    if old_import in PORT_MIGRATIONS:
        mapping = PORT_MIGRATIONS[old_import]
        return mapping["new_module"], mapping["new_name"]
    
    # No migration mapping, use old path
    logger.warning(f"No V2 migration mapping for {old_import}")
    parts = old_import.rsplit(".", 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def import_port_dynamically(old_import: str, use_v2: bool = False) -> type:
    """Dynamically import the appropriate port based on feature flag.
    
    Args:
        old_import: The old core.ports import path
        use_v2: Whether to use V2 domain ports
        
    Returns:
        The imported port class
    """
    module_path, class_name = get_port_import(old_import, use_v2)
    
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to import {class_name} from {module_path}: {e}")
        raise


def resolve_port_from_registry(
    registry: Any,
    old_port_name: str,
    use_v2: bool = False
) -> Any:
    """Resolve a port from the service registry.
    
    Args:
        registry: The service registry
        old_port_name: The old port name
        use_v2: Whether to use V2 domain ports
        
    Returns:
        The resolved service instance
    """
    full_import = f"dipeo.core.ports.{old_port_name}"
    
    if not use_v2:
        # Try to resolve using old key
        try:
            return registry.resolve(old_port_name.lower().replace("port", "_service"))
        except:
            pass
    
    # Look up registry token for V2
    if full_import in PORT_MIGRATIONS:
        mapping = PORT_MIGRATIONS[full_import]
        token_name = mapping["registry_token"]
        
        # Import registry tokens module
        from dipeo.application.registry.registry_tokens import (
            STATE_REPOSITORY, STATE_SERVICE, MESSAGE_BUS,
            LLM_SERVICE, LLM_CLIENT, API_INVOKER,
            STORAGE_SERVICE, DOMAIN_EVENT_BUS
        )
        
        # Get the actual token
        token = locals().get(token_name)
        if token:
            try:
                return registry.resolve(token)
            except:
                logger.warning(f"Failed to resolve {token_name} from registry")
    
    # Fallback to old resolution
    return registry.resolve(old_port_name.lower().replace("port", "_service"))


def add_metrics_decorator(func: T) -> T:
    """Add metrics tracking to port method calls.
    
    This decorator tracks:
    - Call count per port/method
    - Execution time
    - Success/failure rate
    - Feature flag usage (V1 vs V2)
    """
    import functools
    import time
    from typing import cast
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        port_name = func.__qualname__.split(".")[0] if hasattr(func, "__qualname__") else "unknown"
        method_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log metrics
            logger.debug(
                f"Port call: {port_name}.{method_name} "
                f"duration={duration:.3f}s status=success"
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.debug(
                f"Port call: {port_name}.{method_name} "
                f"duration={duration:.3f}s status=failure error={type(e).__name__}"
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        port_name = func.__qualname__.split(".")[0] if hasattr(func, "__qualname__") else "unknown"
        method_name = func.__name__
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log metrics
            logger.debug(
                f"Port call: {port_name}.{method_name} "
                f"duration={duration:.3f}s status=success"
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.debug(
                f"Port call: {port_name}.{method_name} "
                f"duration={duration:.3f}s status=failure error={type(e).__name__}"
            )
            raise
    
    # Determine if function is async
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return cast(T, async_wrapper)
    else:
        return cast(T, sync_wrapper)


class PortMigrationHelper:
    """Helper class for migrating ports in a codebase."""
    
    @staticmethod
    def is_v2_enabled(service_name: str) -> bool:
        """Check if V2 is enabled for a service."""
        import os
        
        # Check specific flag
        specific_flag = os.getenv(f"{service_name.upper()}_PORT_V2", "").lower()
        if specific_flag in ["1", "true", "yes", "on"]:
            return True
        if specific_flag in ["0", "false", "no", "off"]:
            return False
        
        # Check global flag
        global_flag = os.getenv("DIPEO_PORT_V2", "0").lower()
        return global_flag in ["1", "true", "yes", "on"]
    
    @staticmethod
    def get_compatible_import(old_import: str) -> tuple[str, str]:
        """Get compatible import based on current feature flags."""
        # Extract service name from import
        if "StateStore" in old_import:
            use_v2 = PortMigrationHelper.is_v2_enabled("state")
        elif "MessageRouter" in old_import:
            use_v2 = PortMigrationHelper.is_v2_enabled("messaging")
        elif "LLM" in old_import:
            use_v2 = PortMigrationHelper.is_v2_enabled("llm")
        elif "Api" in old_import or "API" in old_import:
            use_v2 = PortMigrationHelper.is_v2_enabled("api")
        elif "File" in old_import or "Storage" in old_import:
            use_v2 = PortMigrationHelper.is_v2_enabled("storage")
        elif "Observer" in old_import or "Event" in old_import:
            use_v2 = PortMigrationHelper.is_v2_enabled("events")
        else:
            use_v2 = PortMigrationHelper.is_v2_enabled("global")
        
        return get_port_import(old_import, use_v2)
    
    @staticmethod
    def create_compatibility_shim(old_port_class: type, new_port_class: type) -> type:
        """Create a compatibility shim that implements both old and new interfaces."""
        
        class CompatibilityShim:
            """Shim that proxies calls to the appropriate implementation."""
            
            def __init__(self, implementation: Any):
                self._impl = implementation
            
            def __getattr__(self, name: str):
                # Proxy all attribute access to implementation
                return getattr(self._impl, name)
        
        # Copy interface from both old and new
        for attr_name in dir(old_port_class):
            if not attr_name.startswith("_"):
                if not hasattr(CompatibilityShim, attr_name):
                    setattr(CompatibilityShim, attr_name, 
                           lambda self, *a, **k: getattr(self._impl, attr_name)(*a, **k))
        
        for attr_name in dir(new_port_class):
            if not attr_name.startswith("_"):
                if not hasattr(CompatibilityShim, attr_name):
                    setattr(CompatibilityShim, attr_name,
                           lambda self, *a, **k: getattr(self._impl, attr_name)(*a, **k))
        
        return CompatibilityShim