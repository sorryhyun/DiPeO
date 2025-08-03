"""
Strawberry GraphQL types for DiPeO domain models.
Temporary file to register domain types used by node data models.
"""

import strawberry
from dipeo.diagram_generated.domain_models import MemorySettings
from dipeo.diagram_generated.integrations import ToolConfig
from dipeo.diagram_generated.enums import MemoryView, ToolType


@strawberry.experimental.pydantic.type(MemorySettings, all_fields=True)
class MemorySettingsType:
    """Memory settings for AI agents"""
    pass


@strawberry.experimental.pydantic.type(ToolConfig, all_fields=True)
class ToolConfigType:
    """Tool configuration for AI agents"""
    pass