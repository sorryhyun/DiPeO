"""GraphQL type definitions for DiPeO.

Re-exports generated types from dipeo.diagram_generated and adds
additional GraphQL-specific types needed for the schema.
"""

# Re-export all generated domain types
from dipeo.diagram_generated.domain_models import *  # noqa: F403
from dipeo.diagram_generated.enums import *  # noqa: F403
from dipeo.diagram_generated.graphql import *  # noqa: F403

# Import Strawberry domain types from generated code
from dipeo.diagram_generated.graphql.domain_types import (
    DiagramMetadataType,
    DomainApiKeyType,
    DomainArrowType,
    DomainDiagramType,
    DomainHandleType,
    DomainNodeType,
    DomainPersonType,
    EnvelopeMetaType,
    ExecutionOptionsType,
    ExecutionStateType,
    LLMUsageType,
    NodeStateType,
    PersonLLMConfigType,
    SerializedEnvelopeType,
    SerializedNodeOutputType,
    ToolConfigType,
    Vec2Type,
)

# Import generated scalars instead of manual ones
from dipeo.diagram_generated.graphql.scalars import *  # noqa: F403
from dipeo.diagram_generated.models.api_job_model import ApiJobNodeData
from dipeo.diagram_generated.models.code_job_model import CodeJobNodeData
from dipeo.diagram_generated.models.condition_model import ConditionNodeData
from dipeo.diagram_generated.models.db_model import DbNodeData
from dipeo.diagram_generated.models.endpoint_model import EndpointNodeData
from dipeo.diagram_generated.models.hook_model import HookNodeData
from dipeo.diagram_generated.models.json_schema_validator_model import JsonSchemaValidatorNodeData
from dipeo.diagram_generated.models.person_batch_job_model import PersonBatchJobNodeData
from dipeo.diagram_generated.models.person_job_model import PersonJobNodeData

# Import specific node data types
from dipeo.diagram_generated.models.start_model import StartNodeData
from dipeo.diagram_generated.models.sub_diagram_model import SubDiagramNodeData
from dipeo.diagram_generated.models.template_job_model import TemplateJobNodeData
from dipeo.diagram_generated.models.typescript_ast_model import TypescriptAstNodeData
from dipeo.diagram_generated.models.user_response_model import UserResponseNodeData

# Import GraphQL-specific types
from .inputs import *  # noqa: F403
from .results import *  # noqa: F403

__all__ = [
    "ApiJobNodeData",
    "CodeJobNodeData",
    "ConditionNodeData",
    "DbNodeData",
    "DiagramMetadataType",
    "DomainApiKeyType",
    "DomainArrowType",
    # Domain types
    "DomainDiagramType",
    "DomainHandleType",
    "DomainNodeType",
    "DomainPersonType",
    "EndpointNodeData",
    "EnvelopeMetaType",
    "ExecutionOptionsType",
    "ExecutionStateType",
    "HookNodeData",
    "JsonSchemaValidatorNodeData",
    "LLMUsageType",
    "NodeStateType",
    "PersonBatchJobNodeData",
    "PersonJobNodeData",
    "PersonLLMConfigType",
    "SerializedEnvelopeType",
    "SerializedNodeOutputType",
    # Node data types
    "StartNodeData",
    "SubDiagramNodeData",
    "TemplateJobNodeData",
    "ToolConfigType",
    "TypescriptAstNodeData",
    "UserResponseNodeData",
    "Vec2Type",
]
