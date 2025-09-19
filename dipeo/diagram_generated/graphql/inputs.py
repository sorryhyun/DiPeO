"""
GraphQL input types for DiPeO mutations.
Auto-generated from TypeScript definitions.

Generated at: 2025-09-19T17:28:43.378161
"""

from datetime import datetime
from typing import Optional, List, Any
from strawberry.scalars import JSON, ID

import strawberry
from .enums import DiagramFormatGraphQL

# Import basic scalar type aliases for Strawberry
String = str
Int = int
Float = float
Boolean = bool
DateTime = datetime

# Import enums from generated modules
from dipeo.diagram_generated.enums import APIServiceType, LLMService, NodeType, Status, DiagramFormat, TodoSyncMode

# Import scalars to ensure they're registered
from dipeo.diagram_generated.graphql.scalars import *



@strawberry.input
class Vec2Input:
    x: Float
    y: Float


@strawberry.input
class PersonLLMConfigInput:
    api_key_id: ID
    model: String
    service: LLMService
    system_prompt: Optional[String] = None


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
    author: Optional[String] = None
    description: Optional[String] = None
    name: String
    tags: Optional[List[String]] = None


@strawberry.input
class DiagramFilterInput:
    author: Optional[String] = None
    created_after: Optional[DateTime] = None
    created_before: Optional[DateTime] = None
    name: Optional[String] = None
    tags: Optional[List[String]] = None


@strawberry.input
class CreatePersonInput:
    label: String
    llm_config: PersonLLMConfigInput
    type: Optional[String] = None


@strawberry.input
class UpdatePersonInput:
    label: Optional[String] = None
    llm_config: Optional[PersonLLMConfigInput] = None


@strawberry.input
class CreateApiKeyInput:
    key: String
    label: String
    service: APIServiceType


@strawberry.input
class ExecuteDiagramInput:
    debug_mode: Optional[Boolean] = None
    diagram_data: Optional[JSON] = None
    diagram_id: Optional[ID] = None
    max_iterations: Optional[Int] = None
    timeout_seconds: Optional[Int] = None
    use_unified_monitoring: Optional[Boolean] = None
    variables: Optional[JSON] = None


@strawberry.input
class ExecutionControlInput:
    action: String
    execution_id: ID
    reason: Optional[String] = None


@strawberry.input
class ExecutionFilterInput:
    diagram_id: Optional[ID] = None
    started_after: Optional[DateTime] = None
    started_before: Optional[DateTime] = None
    status: Optional[Status] = None


@strawberry.input
class UpdateNodeStateInput:
    error: Optional[String] = None
    execution_id: ID
    node_id: ID
    output: Optional[JSON] = None
    status: Status


@strawberry.input
class InteractiveResponseInput:
    execution_id: ID
    metadata: Optional[JSON] = None
    node_id: ID
    response: String


@strawberry.input
class RegisterCliSessionInput:
    execution_id: ID
    diagram_name: String
    diagram_format: DiagramFormatGraphQL
    diagram_data: Optional[JSON] = None


@strawberry.input
class UnregisterCliSessionInput:
    execution_id: ID


@strawberry.input
class ToggleTodoSyncInput:
    session_id: String
    enabled: Boolean
    trace_id: Optional[String] = None


@strawberry.input
class ConfigureTodoSyncInput:
    mode: TodoSyncMode
    output_dir: Optional[String] = None
    auto_execute: Optional[Boolean] = None
    monitor_enabled: Optional[Boolean] = None
    debounce_seconds: Optional[Float] = None


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
    'ToggleTodoSyncInput',
    'ConfigureTodoSyncInput',
]
