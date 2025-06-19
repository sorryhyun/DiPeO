"""
Enhanced domain models for GraphQL integration using Pydantic as single source of truth.
These models will be used with @strawberry.experimental.pydantic.type decorator.
"""
from typing import Dict, Optional, List, Any, Union, Final, NewType
from pydantic import BaseModel, Field, computed_field, ConfigDict
from datetime import datetime
from enum import Enum

# Import all models from generated code
from src.__generated__.models import (
    # Core Models
    DomainNode,
    DomainArrow, 
    DomainHandle,
    DomainPerson,
    DomainApiKey,
    DomainDiagram,
    DiagramDictFormat,
    DiagramMetadata,
    # Enums
    NodeType,
    HandleDirection,
    DataType,
    LLMService,
    ForgettingMode,
    DiagramFormat,
    ExecutionStatus,
    NodeExecutionStatus,
    EventType,
    DBBlockSubType,
    ContentType,
    ContextCleaningRule,
    # Type aliases
    NodeID,
    ArrowID,
    HandleID,
    PersonID,
    ApiKeyID,
    DiagramID,
    # Base models
    Vec2,
    # Execution models
    ExecutionState,
    ExecutionEvent,
    ExecutionResult,
    NodeResult,
    # Other models
    PersonConfiguration,
    PersonConversation,
    ConversationMessage,
    ConversationMetadata,
    PersonExecutionContext,
    ExecutionOptions,
    InteractivePromptData,
    InteractiveResponse,
    PersonMemoryMessage,
    PersonMemoryState,
    PersonMemoryConfig,
    ExecutionUpdate,
    # Node data models
    BaseNodeData,
    StartNodeData,
    ConditionNodeData,
    PersonJobNodeData,
    EndpointNodeData,
    DBNodeData,
    JobNodeData,
    UserResponseNodeData,
    NotionNodeData,
)

# Import constants from shared domain (not generated)
from src.common import (
    # Constants
    API_BASE_PATH,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    SUPPORTED_DOC_EXTENSIONS,
    SUPPORTED_CODE_EXTENSIONS,
    SERVICE_TO_PROVIDER_MAP,
    PROVIDER_TO_ENUM_MAP,
    DEFAULT_SERVICE,
)

# Import ExecutionID from shared domain types and TokenUsage from generated models
from src.common.types import ExecutionID
from src.__generated__.models import TokenUsage

# Domain-specific extensions and aliases
# The base models are imported from generated code above

# Use ExtendedTokenUsage as an alias for backward compatibility
ExtendedTokenUsage = TokenUsage

# All other models are now imported from generated code
# Only domain-specific extensions are defined in this file