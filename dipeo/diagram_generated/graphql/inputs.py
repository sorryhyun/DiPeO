"""
GraphQL input types for DiPeO mutations.
Auto-generated from TypeScript definitions.

Generated at: 2025-09-14T17:05:07.432446
"""

from datetime import datetime
from typing import Optional, List, Any
from strawberry.scalars import JSON

import strawberry
from .enums import DiagramFormatGraphQL


# Import enums from generated modules
from dipeo.diagram_generated.enums import APIServiceType, LLMService, NodeType, Status, DiagramFormat

# Import scalars to ensure they're registered
from dipeo.diagram_generated.graphql.scalars import *



@strawberry.input
class Vec2Input:
    x: float
    y: float


@strawberry.input
class PersonLLMConfigInput:
    api_key_id: str
    model: str
    service: LLMService
    system_prompt: Optional[str] = None


@strawberry.input
class CreateNodeInput:
    data: JSON
    position: Vec2Input
    type: NodeType


@strawberry.input
class UpdateNodeInput:
    data: Optional[JSON] = None
    position: Optional[Vec2Input] = None


@strawberry.input
class CreateDiagramInput:
    author: Optional[str] = None
    description: Optional[str] = None
    name: str
    tags: Optional[List[str]] = None


@strawberry.input
class DiagramFilterInput:
    author: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    name: Optional[str] = None
    tags: Optional[List[str]] = None


@strawberry.input
class CreatePersonInput:
    label: str
    llm_config: PersonLLMConfigInput
    type: Optional[str] = None


@strawberry.input
class UpdatePersonInput:
    label: Optional[str] = None
    llm_config: Optional[PersonLLMConfigInput] = None


@strawberry.input
class CreateApiKeyInput:
    key: str
    label: str
    service: APIServiceType


@strawberry.input
class ExecuteDiagramInput:
    debug_mode: Optional[bool] = None
    diagram_data: Optional[JSON] = None
    diagram_id: Optional[str] = None
    max_iterations: Optional[int] = None
    timeout_seconds: Optional[int] = None
    use_unified_monitoring: Optional[bool] = None
    variables: Optional[JSON] = None


@strawberry.input
class ExecutionControlInput:
    action: str
    execution_id: str
    reason: Optional[str] = None


@strawberry.input
class ExecutionFilterInput:
    diagram_id: Optional[str] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    status: Optional[Status] = None


@strawberry.input
class UpdateNodeStateInput:
    error: Optional[str] = None
    execution_id: str
    node_id: str
    output: Optional[JSON] = None
    status: Status


@strawberry.input
class InteractiveResponseInput:
    execution_id: str
    metadata: Optional[JSON] = None
    node_id: str
    response: str


@strawberry.input
class RegisterCliSessionInput:
    execution_id: str
    diagram_name: str
    diagram_format: DiagramFormatGraphQL
    diagram_data: Optional[JSON] = None


@strawberry.input
class UnregisterCliSessionInput:
    execution_id: str


# Export all input types
__all__ = [
    'Vec2Input',
    'PersonLLMConfigInput',
    'CreateNodeInput',
    'UpdateNodeInput',
    'CreateDiagramInput',
    'DiagramFilterInput',
    'CreatePersonInput',
    'UpdatePersonInput',
    'CreateApiKeyInput',
    'ExecuteDiagramInput',
    'ExecutionControlInput',
    'ExecutionFilterInput',
    'UpdateNodeStateInput',
    'InteractiveResponseInput',
    'RegisterCliSessionInput',
    'UnregisterCliSessionInput',
]