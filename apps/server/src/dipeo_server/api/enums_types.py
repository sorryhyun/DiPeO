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
from dipeo_server.core import DiagramFormat as DomainDiagramFormat

# Create strawberry enum from domain enum
DiagramFormat = strawberry.enum(DomainDiagramFormat)

# EventType is already defined in generated models and will be auto-converted by Strawberry