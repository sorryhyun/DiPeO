"""Application-layer service registry for DiPeO."""

from .enhanced_service_registry import (
    ChildServiceRegistry,
)
from .enhanced_service_registry import (
    EnhancedServiceKey as ServiceKey,
)
from .enhanced_service_registry import (
    EnhancedServiceRegistry as ServiceRegistry,
)
from .keys import *

__all__ = [
    "ServiceRegistry",
    "ServiceKey",
    "ChildServiceRegistry",
] + [
    item
    for item in dir()
    if item.endswith("_SERVICE")
    or item.endswith("_STORE")
    or item.endswith("_REPOSITORY")
    or item.endswith("_ADAPTER")
    or item.endswith("_CACHE")
    or item.endswith("_BUS")
    or item.endswith("_REGISTRY")
    or item.endswith("_USE_CASE")
    or item.endswith("_ENGINE")
    or item.endswith("_ORCHESTRATOR")
    or item.endswith("_SELECTOR")
    or item.endswith("_PROCESSOR")
    or item.endswith("_INVOKER")
    or item.endswith("_PARSER")
    or item == "DATABASE"
    or item == "DIAGRAM"
    or item == "EXECUTION_CONTEXT"
    or item == "CURRENT_NODE_INFO"
    or item == "NODE_EXEC_COUNTS"
    or item == "NOTION_CLIENT"
]
