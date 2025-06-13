"""
REST API deprecation configuration.

This module controls which REST endpoints are enabled during the GraphQL migration.
"""

import os
from typing import Set

# Feature flags for REST endpoints
ENABLE_DEPRECATED_REST = os.environ.get("ENABLE_DEPRECATED_REST", "true").lower() == "true"
ENABLE_HEALTH_ENDPOINTS = True  # Always enabled for Kubernetes
ENABLE_WEBSOCKET = True  # Keep until CLI is migrated

# Granular control over specific routers
ENABLED_ROUTERS: Set[str] = set()

if ENABLE_DEPRECATED_REST:
    # Enable all routers during transition period
    ENABLED_ROUTERS.update([
        "diagram",
        "apikeys", 
        "files",
        "conversations",
        "models"
    ])

if ENABLE_HEALTH_ENDPOINTS:
    ENABLED_ROUTERS.add("health")

if ENABLE_WEBSOCKET:
    ENABLED_ROUTERS.add("websocket")

def is_router_enabled(router_name: str) -> bool:
    """Check if a specific router is enabled."""
    return router_name in ENABLED_ROUTERS

# Deprecation warnings
DEPRECATION_MESSAGE = """
This REST endpoint has been migrated to GraphQL and will be removed in a future version.
Please use the GraphQL endpoint at /graphql instead.
See the migration guide for more information.
"""