# Validation rules for diagram resolution and execution

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from dipeo.models import HandleLabel, NodeID, NodeType


class ValidationSeverity(Enum):
    # Severity levels for validation issues
    ERROR = "error"      # Must be fixed before execution
    WARNING = "warning"  # Should be reviewed but won't block execution
    INFO = "info"        # Informational, no action required


@dataclass
class ValidationIssue:
    # A validation issue found during diagram validation
    severity: ValidationSeverity
    category: str
    message: str
    node_id: NodeID | None = None
    details: dict[str, Any] | None = None


class NodeValidator(Protocol):
    # Protocol for node-specific validators
    
    def validate(self, node: Any) -> list[ValidationIssue]:
        # Validate a node and return any issues found
        ...


class ValidationRules:
    # Central validation rules for diagram resolution
    
    # Node type constraints
    NODE_CONNECTION_RULES = {
        NodeType.start: {
            "max_inputs": 0,
            "max_outputs": None,
            "required_handles": [HandleLabel.default],
            "allowed_targets": [NodeType.person_job, NodeType.condition, NodeType.db, NodeType.code_job]
        },
        NodeType.endpoint: {
            "max_inputs": None,
            "max_outputs": 0,
            "required_handles": [HandleLabel.default],
            "allowed_sources": None  # Any node can connect to endpoint
        },
        NodeType.person_job: {
            "max_inputs": None,
            "max_outputs": None,
            "required_handles": [HandleLabel.default],
            "allowed_targets": None,  # Can connect to any node
            "allowed_sources": None   # Any node can connect
        },
        NodeType.condition: {
            "max_inputs": 1,  # Conditions typically have single input
            "max_outputs": None,  # Multiple branches allowed
            "required_handles": [HandleLabel.default, HandleLabel.condtrue, HandleLabel.condfalse],
            "allowed_targets": None,
            "allowed_sources": [NodeType.person_job, NodeType.code_job, NodeType.db]
        },
        NodeType.db: {
            "max_inputs": None,
            "max_outputs": None,
            "required_handles": [],  # DB nodes have dynamic handles
            "allowed_targets": None,
            "allowed_sources": None
        }
    }
    
    # Execution constraints
    MAX_PARALLEL_NODES = 10  # Maximum nodes executing in parallel
    MAX_RECURSION_DEPTH = 50  # Maximum execution depth
    MAX_TOTAL_NODES = 1000  # Maximum nodes in a diagram
    
    @classmethod
    def validate_node_connections(
        cls,
        node_type: NodeType,
        incoming_count: int,
        outgoing_count: int
    ) -> list[ValidationIssue]:
        # Validate node connection counts
        issues = []
        rules = cls.NODE_CONNECTION_RULES.get(node_type, {})
        
        # Check input constraints
        max_inputs = rules.get("max_inputs")
        if max_inputs is not None and incoming_count > max_inputs:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="connection",
                message=f"{node_type.value} node cannot have more than {max_inputs} inputs, found {incoming_count}"
            ))
        
        # Check output constraints
        max_outputs = rules.get("max_outputs")
        if max_outputs is not None and outgoing_count > max_outputs:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="connection",
                message=f"{node_type.value} node cannot have more than {max_outputs} outputs, found {outgoing_count}"
            ))
        
        # Special rules
        if node_type == NodeType.start and incoming_count > 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="connection",
                message="Start nodes cannot have incoming connections"
            ))
        
        if node_type == NodeType.endpoint and outgoing_count > 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="connection",
                message="Endpoint nodes cannot have outgoing connections"
            ))
        
        return issues
    
    @classmethod
    def validate_node_handles(
        cls,
        node_type: NodeType,
        available_handles: set[HandleLabel]
    ) -> list[ValidationIssue]:
        # Validate that a node has required handles
        issues = []
        rules = cls.NODE_CONNECTION_RULES.get(node_type, {})
        required_handles = set(rules.get("required_handles", []))
        
        # Skip handle validation if no handles provided (backward compatibility)
        if not available_handles and required_handles:
            # Only warn, don't error
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="handle",
                message=f"{node_type.value} node has no handles defined (expected: {required_handles})"
            ))
            return issues
        
        missing_handles = required_handles - available_handles
        if missing_handles:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="handle",
                message=f"{node_type.value} node missing required handles: {missing_handles}"
            ))
        
        return issues
    
    @classmethod
    def validate_connection_types(
        cls,
        source_type: NodeType,
        target_type: NodeType
    ) -> list[ValidationIssue]:
        # Validate that a connection between node types is allowed
        issues = []
        source_rules = cls.NODE_CONNECTION_RULES.get(source_type, {})
        target_rules = cls.NODE_CONNECTION_RULES.get(target_type, {})
        
        # Check if source can connect to target
        allowed_targets = source_rules.get("allowed_targets")
        if allowed_targets is not None and target_type not in allowed_targets:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="connection_type",
                message=f"{source_type.value} typically doesn't connect to {target_type.value}"
            ))
        
        # Check if target can receive from source
        allowed_sources = target_rules.get("allowed_sources")
        if allowed_sources is not None and source_type not in allowed_sources:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="connection_type",
                message=f"{target_type.value} typically doesn't receive from {source_type.value}"
            ))
        
        return issues
    
    @classmethod
    def validate_execution_groups(
        cls,
        groups: list[Any]
    ) -> list[ValidationIssue]:
        # Validate execution groups for constraints
        issues = []
        
        for group in groups:
            if len(group.nodes) > cls.MAX_PARALLEL_NODES:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="performance",
                    message=f"Execution group {group.level} has {len(group.nodes)} parallel nodes, "
                           f"exceeding recommended maximum of {cls.MAX_PARALLEL_NODES}",
                    details={"group_level": group.level, "node_count": len(group.nodes)}
                ))
        
        return issues
    
    @classmethod
    def validate_diagram_size(
        cls,
        node_count: int,
        edge_count: int
    ) -> list[ValidationIssue]:
        # Validate overall diagram size constraints
        issues = []
        
        if node_count > cls.MAX_TOTAL_NODES:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="size",
                message=f"Diagram has {node_count} nodes, exceeding maximum of {cls.MAX_TOTAL_NODES}"
            ))
        
        # Check for complexity warnings
        if node_count > 100:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="complexity",
                message=f"Large diagram with {node_count} nodes may have performance implications"
            ))
        
        if edge_count > node_count * 3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="complexity",
                message=f"High edge-to-node ratio ({edge_count}/{node_count}) indicates complex interconnections"
            ))
        
        return issues
    
    @classmethod
    def validate_person_node(cls, node_data: dict[str, Any]) -> list[ValidationIssue]:
        # Validate person node specific requirements
        issues = []
        
        # Check for person identification in various formats
        if not any([
            node_data.get("personId"),
            node_data.get("person_id"), 
            node_data.get("person")
        ]):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="configuration",
                message="Person node must have a personId or person reference"
            ))
        
        # Check for prompts - person_job nodes use default_prompt and first_only_prompt
        has_prompt = any([
            node_data.get("prompt"),
            node_data.get("default_prompt"),
            node_data.get("first_only_prompt"),
            node_data.get("useLatestMessage")
        ])
        
        if not has_prompt:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="configuration",
                message="Person node has no prompt and useLatestMessage is false"
            ))
        
        return issues
    
    @classmethod
    def validate_condition_node(cls, node_data: dict[str, Any]) -> list[ValidationIssue]:
        # Validate condition node specific requirements
        issues = []
        
        # Check for condition in various formats
        if not any([
            node_data.get("condition"),
            node_data.get("expression"),
            node_data.get("condition_type")
        ]):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="configuration",
                message="Condition node must have a condition expression or type"
            ))
        
        return issues