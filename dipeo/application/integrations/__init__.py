"""Integrations bounded context in application layer.

This module handles:
- API key management
- External API invocations
- API provider registry
- Rate limiting and HTTP client management
"""

from .wiring import wire_integrations

__all__ = ["wire_integrations"]