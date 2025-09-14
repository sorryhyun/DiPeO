"""
Strawberry GraphQL types for DiPeO domain models.
Temporary file to register domain types used by node data models.
"""

import strawberry
from strawberry.scalars import JSON as JSONScalar
from typing import Any, Optional

from dipeo.diagram_generated.domain_models import ToolConfig, TemplatePreprocessor, JsonDictValidation as JsonDict, RecordStringString


# Register JsonDict as a JSON scalar type
JsonDictScalar = strawberry.scalar(
    JsonDict,
    serialize=lambda v: {} if v is None else dict(v) if hasattr(v, '__dict__') else v,
    parse_value=lambda v: JsonDict() if v is None or v == {} else v,
    description="Generic JSON dictionary"
)

# Register RecordStringString as a JSON scalar type
RecordStringStringScalar = strawberry.scalar(
    RecordStringString,
    serialize=lambda v: {} if v is None else dict(v) if hasattr(v, '__dict__') else v,
    parse_value=lambda v: RecordStringString() if v is None or v == {} else v,
    description="Record of string to string mappings"
)


@strawberry.experimental.pydantic.type(ToolConfig, all_fields=True)
class ToolConfigType:
    """Tool configuration for AI agents"""
    pass


@strawberry.type
class TemplatePreprocessorType:
    """Configuration for template preprocessor"""
    function: str
    module: str
    args: Optional[JSONScalar] = None
    
    @staticmethod
    def from_pydantic(obj: TemplatePreprocessor) -> "TemplatePreprocessorType":
        """Convert from Pydantic model"""
        result = TemplatePreprocessorType(
            function=obj.function,
            module=obj.module,
            args=dict(obj.args) if obj.args and hasattr(obj.args, '__dict__') else obj.args
        )
        return result