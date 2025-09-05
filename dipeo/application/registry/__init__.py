"""Application-layer service registry for DiPeO."""

from .keys import *
from .service_registry import ChildServiceRegistry, ServiceKey, ServiceRegistry

__all__ = [
    "ServiceRegistry",
    "ServiceKey",
    "ChildServiceRegistry",
] + [
    item
    for item in dir()
    if item.endswith("_SERVICE")
    or item.endswith("_STORE")
    or item.endswith("_VALIDATOR")
    or item.endswith("_LOGIC")
    or item == "DATABASE"
    or item == "DIAGRAM"
    or item == "EXECUTION_CONTEXT"
    or item == "CURRENT_NODE_INFO"
    or item == "NODE_EXEC_COUNTS"
    or item == "AST_PARSER"
    or item == "NOTION_CLIENT"
]
