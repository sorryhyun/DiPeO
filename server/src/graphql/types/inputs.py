"""Refactored input types for GraphQL mutations using Pydantic models."""
import strawberry
from typing import Optional, List
from datetime import datetime

from ...models.input_models import (
    Vec2Input as PydanticVec2Input,
    CreateNodeInput as PydanticCreateNodeInput,
    UpdateNodeInput as PydanticUpdateNodeInput,
    CreateHandleInput as PydanticCreateHandleInput,
    CreateArrowInput as PydanticCreateArrowInput,
    CreatePersonInput as PydanticCreatePersonInput,
    UpdatePersonInput as PydanticUpdatePersonInput,
    CreateApiKeyInput as PydanticCreateApiKeyInput,
    CreateDiagramInput as PydanticCreateDiagramInput,
    ExecuteDiagramInput as PydanticExecuteDiagramInput,
    ExecutionControlInput as PydanticExecutionControlInput,
    InteractiveResponseInput as PydanticInteractiveResponseInput,
    DiagramFilterInput as PydanticDiagramFilterInput,
    ExecutionFilterInput as PydanticExecutionFilterInput,
    FileUploadInput as PydanticFileUploadInput,
    ImportYamlInput as PydanticImportYamlInput,
)

from .scalars import (
    NodeID, HandleID, ArrowID, PersonID, ApiKeyID, 
    DiagramID, ExecutionID, JSONScalar
)
from .enums import (
    NodeType, HandleDirection, DataType, LLMService, 
    ForgettingMode, ExecutionStatus
)


# Convert Pydantic input models to Strawberry GraphQL inputs
@strawberry.experimental.pydantic.input(model=PydanticVec2Input, all_fields=True)
class Vec2Input:
    pass

@strawberry.experimental.pydantic.input(model=PydanticCreateNodeInput, all_fields=True)
class CreateNodeInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticUpdateNodeInput, all_fields=True)
class UpdateNodeInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticCreateHandleInput, all_fields=True)
class CreateHandleInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticCreateArrowInput, all_fields=True)
class CreateArrowInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticCreatePersonInput, all_fields=True)
class CreatePersonInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticUpdatePersonInput, all_fields=True)
class UpdatePersonInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticCreateApiKeyInput, all_fields=True)
class CreateApiKeyInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticCreateDiagramInput, all_fields=True)
class CreateDiagramInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticExecuteDiagramInput, all_fields=True)
class ExecuteDiagramInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticExecutionControlInput, all_fields=True)
class ExecutionControlInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticInteractiveResponseInput, all_fields=True)
class InteractiveResponseInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticDiagramFilterInput, all_fields=True)
class DiagramFilterInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticExecutionFilterInput, all_fields=True)
class ExecutionFilterInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticFileUploadInput, all_fields=True)
class FileUploadInput:
    pass

@strawberry.experimental.pydantic.input(model=PydanticImportYamlInput, all_fields=True)
class ImportYamlInput:
    pass