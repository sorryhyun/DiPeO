"""Refactored input types for GraphQL mutations using Pydantic models."""

from typing import Optional

import strawberry

from .models.input_models import (
    CreateApiKeyInput as PydanticCreateApiKeyInput,
)
from .models.input_models import (
    CreateArrowInput as PydanticCreateArrowInput,
)
from .models.input_models import (
    CreateDiagramInput as PydanticCreateDiagramInput,
)
from .models.input_models import (
    CreateHandleInput as PydanticCreateHandleInput,
)
from .models.input_models import (
    CreateNodeInput as PydanticCreateNodeInput,
)
from .models.input_models import (
    CreatePersonInput as PydanticCreatePersonInput,
)
from .models.input_models import (
    DiagramFilterInput as PydanticDiagramFilterInput,
)
from .models.input_models import (
    ExecuteDiagramInput as PydanticExecuteDiagramInput,
)
from .models.input_models import (
    ExecutionControlInput as PydanticExecutionControlInput,
)
from .models.input_models import (
    ExecutionFilterInput as PydanticExecutionFilterInput,
)
from .models.input_models import (
    FileUploadInput as PydanticFileUploadInput,
)
from .models.input_models import (
    ImportYamlInput as PydanticImportYamlInput,
)
from .models.input_models import (
    InteractiveResponseInput as PydanticInteractiveResponseInput,
)
from .models.input_models import (
    UpdateNodeInput as PydanticUpdateNodeInput,
)
from .models.input_models import (
    UpdatePersonInput as PydanticUpdatePersonInput,
)
from .models.input_models import (
    Vec2Input as PydanticVec2Input,
)
from .scalars_types import DiagramID, JSONScalar

# Enums are handled through Pydantic models, no need to import separately


# Convert Pydantic input models to Strawberry GraphQL inputs
@strawberry.experimental.pydantic.input(model=PydanticVec2Input, all_fields=True)
class Vec2Input:
    pass


@strawberry.experimental.pydantic.input(model=PydanticCreateNodeInput)
class CreateNodeInput:
    type: strawberry.auto
    position: strawberry.auto
    label: strawberry.auto
    properties: Optional[JSONScalar] = None


@strawberry.experimental.pydantic.input(model=PydanticUpdateNodeInput)
class UpdateNodeInput:
    id: strawberry.auto
    position: strawberry.auto
    label: strawberry.auto
    properties: Optional[JSONScalar] = None


@strawberry.experimental.pydantic.input(
    model=PydanticCreateHandleInput, all_fields=True
)
class CreateHandleInput:
    pass


@strawberry.experimental.pydantic.input(model=PydanticCreateArrowInput, all_fields=True)
class CreateArrowInput:
    pass


@strawberry.experimental.pydantic.input(
    model=PydanticCreatePersonInput, all_fields=True
)
class CreatePersonInput:
    pass


@strawberry.experimental.pydantic.input(
    model=PydanticUpdatePersonInput, all_fields=True
)
class UpdatePersonInput:
    pass


@strawberry.experimental.pydantic.input(
    model=PydanticCreateApiKeyInput, all_fields=True
)
class CreateApiKeyInput:
    pass


@strawberry.experimental.pydantic.input(
    model=PydanticCreateDiagramInput, all_fields=True
)
class CreateDiagramInput:
    pass


@strawberry.experimental.pydantic.input(model=PydanticExecuteDiagramInput)
class ExecuteDiagramInput:
    diagram_id: Optional[DiagramID] = None
    diagram_data: Optional[JSONScalar] = None
    variables: Optional[JSONScalar] = None
    debug_mode: strawberry.auto
    timeout_seconds: strawberry.auto
    max_iterations: strawberry.auto


@strawberry.experimental.pydantic.input(
    model=PydanticExecutionControlInput, all_fields=True
)
class ExecutionControlInput:
    pass


@strawberry.experimental.pydantic.input(
    model=PydanticInteractiveResponseInput, all_fields=True
)
class InteractiveResponseInput:
    pass


@strawberry.experimental.pydantic.input(
    model=PydanticDiagramFilterInput, all_fields=True
)
class DiagramFilterInput:
    pass


@strawberry.experimental.pydantic.input(
    model=PydanticExecutionFilterInput, all_fields=True
)
class ExecutionFilterInput:
    pass


@strawberry.experimental.pydantic.input(model=PydanticFileUploadInput, all_fields=True)
class FileUploadInput:
    pass


@strawberry.experimental.pydantic.input(model=PydanticImportYamlInput, all_fields=True)
class ImportYamlInput:
    pass
