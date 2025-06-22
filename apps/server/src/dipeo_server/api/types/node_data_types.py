"""Node data types for different node kinds.

This module provides Strawberry GraphQL wrappers around the generated Pydantic models.
It avoids duplicating type definitions by using the generated models as the source of truth.
"""


import strawberry
from dipeo_domain import (
    ConditionNodeData as PydanticConditionNodeData,
)
from dipeo_domain import (
    DBNodeData as PydanticDBNodeData,
)
from dipeo_domain import (
    EndpointNodeData as PydanticEndpointNodeData,
)
from dipeo_domain import (
    JobNodeData as PydanticJobNodeData,
)
from dipeo_domain import (
    NotionNodeData as PydanticNotionNodeData,
)
from dipeo_domain import (
    NotionPageReference as PydanticNotionPageReference,
)
from dipeo_domain import (
    PersonBatchJobNodeData as PydanticPersonBatchJobNodeData,
)
from dipeo_domain import (
    PersonJobNodeData as PydanticPersonJobNodeData,
)

# Import generated node data models
from dipeo_domain import (
    StartNodeData as PydanticStartNodeData,
)
from dipeo_domain import (
    UserResponseNodeData as PydanticUserResponseNodeData,
)


# Create Strawberry types from Pydantic models
@strawberry.experimental.pydantic.type(model=PydanticStartNodeData, all_fields=True)
class StartNodeData:
    pass


@strawberry.experimental.pydantic.type(model=PydanticPersonJobNodeData, all_fields=True)
class PersonJobNodeData:
    pass


@strawberry.experimental.pydantic.type(model=PydanticConditionNodeData, all_fields=True)
class ConditionNodeData:
    pass


@strawberry.experimental.pydantic.type(model=PydanticJobNodeData, all_fields=True)
class JobNodeData:
    pass


@strawberry.experimental.pydantic.type(model=PydanticEndpointNodeData, all_fields=True)
class EndpointNodeData:
    pass


@strawberry.experimental.pydantic.type(model=PydanticDBNodeData, all_fields=True)
class DBNodeData:
    pass


@strawberry.experimental.pydantic.type(
    model=PydanticUserResponseNodeData, all_fields=True
)
class UserResponseNodeData:
    pass


@strawberry.experimental.pydantic.type(
    model=PydanticNotionPageReference, all_fields=True
)
class NotionPageReference:
    pass


@strawberry.experimental.pydantic.type(model=PydanticNotionNodeData, all_fields=True)
class NotionNodeData:
    pass


@strawberry.experimental.pydantic.type(
    model=PydanticPersonBatchJobNodeData, all_fields=True
)
class PersonBatchJobNodeData:
    pass


# Union type for all node data types
NodeDataUnion = strawberry.union(
    "NodeDataUnion",
    [
        StartNodeData,
        PersonJobNodeData,
        ConditionNodeData,
        JobNodeData,
        EndpointNodeData,
        DBNodeData,
        UserResponseNodeData,
        NotionNodeData,
        PersonBatchJobNodeData,
    ],
)
