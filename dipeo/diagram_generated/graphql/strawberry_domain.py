"""
Strawberry GraphQL types for DiPeO domain models.
Temporary file to register domain types used by node data models.
"""

import strawberry
from dipeo.diagram_generated.domain_models import ToolConfig, TemplatePreprocessor
from dipeo.diagram_generated.enums import ToolType



@strawberry.experimental.pydantic.type(ToolConfig, all_fields=True)
class ToolConfigType:
    """Tool configuration for AI agents"""
    pass


@strawberry.experimental.pydantic.type(TemplatePreprocessor, all_fields=True)
class TemplatePreprocessorType:
    """Configuration for template preprocessor"""
    pass