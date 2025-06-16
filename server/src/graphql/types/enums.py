"""Enum types for DiPeO GraphQL schema.

IMPORTANT: Most enums are defined in models/domain.py as Pydantic enums
and are automatically converted to GraphQL enums by Strawberry when using
@strawberry.experimental.pydantic.type decorator.

This file only contains enums that are specific to GraphQL/subscriptions
and not part of the core domain model.
"""
import strawberry
from enum import Enum

# Import domain enums that need to be exposed in GraphQL
from ...domain import DiagramFormat as DomainDiagramFormat

# Create strawberry enum from domain enum
DiagramFormat = strawberry.enum(DomainDiagramFormat)

# EventType is specific to GraphQL subscriptions and not part of the core domain
@strawberry.enum
class EventType(Enum):
    EXECUTION_STARTED = "execution_started"
    NODE_STARTED = "node_started"
    NODE_RUNNING = "node_running"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    NODE_SKIPPED = "node_skipped"
    NODE_PAUSED = "node_paused"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_ABORTED = "execution_aborted"
    INTERACTIVE_PROMPT = "interactive_prompt"
    INTERACTIVE_RESPONSE = "interactive_response"