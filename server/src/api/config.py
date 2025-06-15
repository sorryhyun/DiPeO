"""
REST API configuration.

This module controls which essential REST endpoints remain enabled.
"""

import os
from typing import Set

# Feature flags for essential REST endpoints
ENABLE_HEALTH_ENDPOINTS = True  # Always enabled for Kubernetes

# WebSocket endpoint control - can be disabled via environment variable
# Set DISABLE_WEBSOCKET=true to disable the WebSocket endpoint
ENABLE_WEBSOCKET = os.environ.get("DISABLE_WEBSOCKET", "false").lower() != "true"

# Only essential routers remain enabled
ENABLED_ROUTERS: Set[str] = set()

if ENABLE_HEALTH_ENDPOINTS:
    ENABLED_ROUTERS.add("health")

if ENABLE_WEBSOCKET:
    ENABLED_ROUTERS.add("websocket")

def is_router_enabled(router_name: str) -> bool:
    """Check if a specific router is enabled."""
    return router_name in ENABLED_ROUTERS