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
    TokenUsage,
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
from src.shared.domain import (
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

# Type for ExecutionID (not in generated models yet)
ExecutionID = NewType('ExecutionID', str)

# Domain-specific extensions and aliases
# The base models are imported from generated code above

# Extended domain model with business logic for dictionary format
class ExtendedDiagramDict(DiagramDictFormat):
    """Main diagram model with dictionaries (internal format) - extended with business logic."""
    
    def to_graphql(self) -> DomainDiagram:
        """Convert to GraphQL-friendly format with lists."""
        return DomainDiagram(
            nodes=list(self.nodes.values()),
            handles=list(self.handles.values()),
            arrows=list(self.arrows.values()),
            persons=list(self.persons.values()),
            api_keys=list(self.api_keys.values()),
            metadata=self.metadata
        )
    
    @classmethod
    def from_graphql(cls, graphql_diagram: DomainDiagram) -> 'ExtendedDiagramDict':
        """Convert from GraphQL format back to domain format."""
        return cls(
            nodes={node.id: node for node in graphql_diagram.nodes},
            handles={handle.id: handle for handle in graphql_diagram.handles},
            arrows={arrow.id: arrow for arrow in graphql_diagram.arrows},
            persons={person.id: person for person in graphql_diagram.persons},
            api_keys={api_key.id: api_key for api_key in graphql_diagram.api_keys},
            metadata=graphql_diagram.metadata
        )
    

# Domain-specific methods for TokenUsage
class ExtendedTokenUsage(TokenUsage):
    """Extended TokenUsage with provider-specific parsing."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return self.model_dump()
    
    @classmethod
    def from_response(cls, response: dict) -> 'ExtendedTokenUsage':
        """Create TokenUsage from LLM response dict"""
        return cls(
            input=response.get("input_tokens", 0),
            output=response.get("output_tokens", 0),
            cached=response.get("cached_tokens", 0)
        )
    
    @classmethod
    def from_usage(cls, usage: Any, service: str = None) -> 'ExtendedTokenUsage':
        """Create from provider-specific usage object"""
        if not usage:
            return cls()
        
        # Handle different provider formats
        if service == "gemini" and isinstance(usage, (list, tuple)):
            return cls(
                input=usage[0] if len(usage) > 0 else 0,
                output=usage[1] if len(usage) > 1 else 0
            )
        
        # Extract tokens based on format
        input_tokens = (getattr(usage, 'input_tokens', None) or
                        getattr(usage, 'prompt_tokens', None) or 0)
        output_tokens = (getattr(usage, 'output_tokens', None) or
                         getattr(usage, 'completion_tokens', None) or 0)
        cached_tokens = 0
        
        # Special handling for OpenAI cached tokens
        if service == "openai":
            # Try to get cached tokens from nested structure
            if hasattr(usage, 'input_tokens_details') and hasattr(usage.input_tokens_details, 'cached_tokens'):
                cached_tokens = usage.input_tokens_details.cached_tokens or 0
        else:
            cached_tokens = getattr(usage, 'cached_tokens', 0)
            
        return cls(
            input=input_tokens,
            output=output_tokens,
            cached=cached_tokens
        )

# All other models are now imported from generated code
# Only domain-specific extensions are defined in this file