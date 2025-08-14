"""Core execution tracking and output management for DiPeO.

This module provides:
- Type-safe node output protocols and implementations
- Execution tracking that separates runtime state from history
- Support for iterative execution without losing state
- Node-type-specific strategies and input resolution
- Executable diagram structures and compilation
- Envelope-based message passing (migration in progress)
"""

from dipeo.core.execution.execution_tracker import (
    CompletionStatus,
    ExecutionTracker,
    FlowStatus,
    NodeExecutionRecord,
    NodeRuntimeState,
)
from dipeo.core.execution.node_output import (
    NodeOutputProtocol,
    serialize_protocol,
    deserialize_protocol,
)
from dipeo.core.execution.envelope import (
    Envelope,
    EnvelopeFactory,
)
from dipeo.core.execution.envelope_reader import (
    EnvelopeReader,
)
from dipeo.core.execution.envelope_output import (
    EnvelopeOutput,
    ConversationEnvelopeOutput,
    ConditionEnvelopeOutput,
    DataEnvelopeOutput,
    create_text_output,
    create_json_output,
    create_error_output,
    create_conversation_output,
    create_condition_output,
    create_data_output,
)
from dipeo.core.execution.node_strategy import (
    NodeStrategy,
    PersonJobNodeStrategy,
    ConditionNodeStrategy,
    DefaultNodeStrategy,
    NodeStrategyRegistry,
    node_strategy_registry,
)
from dipeo.core.ports.diagram_compiler import DiagramCompiler
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableEdgeV2, ExecutableNode, NodeOutputProtocolV2, StandardNodeOutput
from dipeo.core.execution.execution_context import ExecutionContext
from dipeo.core.execution.runtime_resolver import RuntimeResolver, TransformationRule
from dipeo.core.execution.dynamic_order_calculator import DynamicOrderCalculator
from dipeo.core.execution.execution_state_manager import ExecutionStateManager
from dipeo.diagram_generated.generated_nodes import (
    ApiJobNode,
    BaseExecutableNode,
    CodeJobNode,
    ConditionNode,
    DBNode,
    EndpointNode,
    HookNode,
    JsonSchemaValidatorNode,
    PersonBatchJobNode,
    PersonJobNode,
    StartNode,
    SubDiagramNode,
    TemplateJobNode,
    TypescriptAstNode,
    UserResponseNode,
    create_executable_node,
)

__all__ = [
    # Node outputs (protocol only)
    "NodeOutputProtocol",
    "serialize_protocol",
    "deserialize_protocol",
    # Envelope system (new)
    "Envelope",
    "EnvelopeFactory",
    "EnvelopeReader",
    "EnvelopeOutput",
    "ConversationEnvelopeOutput",
    "ConditionEnvelopeOutput",
    "DataEnvelopeOutput",
    "create_text_output",
    "create_json_output",
    "create_error_output",
    "create_conversation_output",
    "create_condition_output",
    "create_data_output",
    # Execution tracking
    "ExecutionTracker",
    "FlowStatus",
    "CompletionStatus",
    "NodeExecutionRecord",
    "NodeRuntimeState",
    # Node strategies
    "NodeStrategy",
    "PersonJobNodeStrategy",
    "ConditionNodeStrategy",
    "DefaultNodeStrategy",
    "NodeStrategyRegistry",
    "node_strategy_registry",
    # Diagram structures
    "ExecutableDiagram",
    "ExecutableEdgeV2",
    "ExecutableNode",
    "NodeOutputProtocolV2",
    "StandardNodeOutput",
    # Node types
    "BaseExecutableNode",
    "StartNode",
    "PersonJobNode",
    "PersonBatchJobNode",
    "ConditionNode",
    "CodeJobNode",
    "ApiJobNode",
    "EndpointNode",
    "DBNode",
    "UserResponseNode",
    "HookNode",
    "JsonSchemaValidatorNode",
    "SubDiagramNode",
    "TemplateJobNode",
    "TypescriptAstNode",
    # Factory
    "create_executable_node",
    # Protocols and base classes
    "DiagramCompiler",
    "ExecutionContext",
    "RuntimeResolver",
    "TransformationRule",
    "DynamicOrderCalculator",
    "ExecutionStateManager",
]