# Validation rules for diagram resolution and execution
# DEPRECATED: This module is deprecated. Use dipeo.domain.diagram.validation.constraints instead.

import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from dipeo.diagram_generated import HandleLabel, NodeID, NodeType
from dipeo.domain.diagram.validation.constraints import GeneratedConstraints

warnings.warn(
    "dipeo.domain.validators.validation_rules is deprecated. "
    "Use dipeo.domain.diagram.validation.constraints.GeneratedConstraints instead.",
    DeprecationWarning,
    stacklevel=2
)


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


class ValidationRules(GeneratedConstraints):
    # Central validation rules for diagram resolution
    # DEPRECATED: This class now delegates to GeneratedConstraints
    
    # Node type constraints - now generated dynamically
    @property 
    def NODE_CONNECTION_RULES(self):
        # Return dict-like interface for backward compatibility
        result = {}
        for node_type in NodeType:
            constraint = self.get_constraint(node_type)
            result[node_type] = {
                "max_inputs": constraint.max_inputs,
                "max_outputs": constraint.max_outputs, 
                "required_handles": list(constraint.required_handles) if constraint.required_handles else [],
                "allowed_sources": list(constraint.allowed_sources) if constraint.allowed_sources else None,
                "allowed_targets": list(constraint.allowed_targets) if constraint.allowed_targets else None,
            }
        return result
    
    @classmethod
    def validate_node_connections(
        cls,
        node_type: NodeType,
        incoming_count: int,
        outgoing_count: int
    ) -> list[ValidationIssue]:
        # Validate node connection counts using generated constraints
        issues = []
        
        # Get constraints from GeneratedConstraints
        max_inputs = cls.get_max_inputs(node_type)
        max_outputs = cls.get_max_outputs(node_type)
        
        # Check input constraints
        if max_inputs is not None and incoming_count > max_inputs:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="connection",
                message=f"{node_type.value} node cannot have more than {max_inputs} inputs, found {incoming_count}"
            ))
        
        # Check output constraints
        if max_outputs is not None and outgoing_count > max_outputs:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="connection",
                message=f"{node_type.value} node cannot have more than {max_outputs} outputs, found {outgoing_count}"
            ))
        
        # Special rules (these are already encoded in constraints)
        if node_type == NodeType.START and incoming_count > 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="connection",
                message="Start nodes cannot have incoming connections"
            ))
        
        if node_type == NodeType.ENDPOINT and outgoing_count > 0:
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
        # Validate that a node has required handles using generated constraints
        issues = []
        required_handles = cls.get_required_handles(node_type)
        
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
        # Validate that a connection between node types is allowed using generated constraints
        issues = []
        
        # Use the can_connect method from GeneratedConstraints
        if not cls.can_connect(source_type, target_type):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="connection_type",
                message=f"Connection from {source_type.value} to {target_type.value} may not be allowed"
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