"""
Strawberry GraphQL types using Pydantic models as single source of truth.
This replaces the manual type definitions with automatic conversions.
"""
import strawberry
from typing import Optional, List, Any

from ...models.domain_graphql import (
    DomainHandle, DomainNode, DomainArrow, DomainPerson,
    DomainApiKey, DiagramMetadata, DiagramForGraphQL,
    ExecutionState as PydanticExecutionState,
    ExecutionEvent as PydanticExecutionEvent,
    TokenUsage as PydanticTokenUsage,
    Vec2 as PydanticVec2
)

# Convert basic types
@strawberry.experimental.pydantic.type(model=PydanticVec2, all_fields=True)
class Vec2:
    """2D position vector."""
    pass

@strawberry.experimental.pydantic.type(model=PydanticTokenUsage, all_fields=True)
class TokenUsage:
    """Token usage statistics."""
    pass

# Convert domain models to Strawberry types
@strawberry.experimental.pydantic.type(model=DomainHandle, all_fields=True)
class Handle:
    """Connection point on a node."""
    pass

@strawberry.experimental.pydantic.type(model=DomainNode, all_fields=True)
class Node:
    """Node in a diagram."""
    pass

@strawberry.experimental.pydantic.type(model=DomainArrow, all_fields=True)
class Arrow:
    """Connection between two handles."""
    pass

@strawberry.experimental.pydantic.type(model=DomainPerson, all_fields=True)
class Person:
    """Person (LLM agent) configuration."""
    pass

@strawberry.experimental.pydantic.type(model=DomainApiKey, all_fields=True)
class ApiKey:
    """API key configuration - excludes actual key."""
    pass

@strawberry.experimental.pydantic.type(model=DiagramMetadata, all_fields=True)
class DiagramMetadata:
    """Metadata for a diagram."""
    pass

@strawberry.experimental.pydantic.type(model=DiagramForGraphQL, all_fields=True)
class Diagram:
    """Complete diagram with all components."""
    # The async field needs special handling
    @strawberry.field
    async def estimated_cost(self, info) -> Optional[float]:
        """Estimated execution cost based on LLM usage."""
        # TODO: Calculate based on persons and their models
        return None

@strawberry.experimental.pydantic.type(model=PydanticExecutionState, all_fields=True)
class ExecutionState:
    """Current state of a diagram execution."""
    pass

@strawberry.experimental.pydantic.type(model=PydanticExecutionEvent, all_fields=True)
class ExecutionEvent:
    """Event during diagram execution."""
    pass

# Re-export the enums from GraphQL enums (these need special handling)
from .enums import (
    NodeType as GraphQLNodeType,
    HandleDirection as GraphQLHandleDirection,
    DataType as GraphQLDataType,
    LLMService as GraphQLLLMService,
    ForgettingMode as GraphQLForgettingMode,
    ExecutionStatus as GraphQLExecutionStatus,
    EventType as GraphQLEventType
)