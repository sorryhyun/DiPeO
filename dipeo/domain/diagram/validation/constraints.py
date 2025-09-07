"""
Generated constraints for node validation based on node types.

This module dynamically generates validation constraints from the node type definitions,
replacing the hardcoded rules in validation_rules.py.
"""

from dataclasses import dataclass

from dipeo.diagram_generated import HandleLabel, NodeType


@dataclass(frozen=True)
class NodeConstraint:
    """Constraints for a specific node type."""

    max_inputs: int | None = None
    max_outputs: int | None = None
    required_handles: set[HandleLabel] = None
    allowed_sources: set[NodeType] | None = None
    allowed_targets: set[NodeType] | None = None

    def __post_init__(self):
        # Ensure required_handles is always a set
        if self.required_handles is None:
            object.__setattr__(self, "required_handles", set())


class GeneratedConstraints:
    """
    Dynamically generated constraints based on node types.

    This replaces the hardcoded NODE_CONNECTION_RULES from validation_rules.py
    with constraints derived from the actual node type definitions.
    """

    # Node type constraints generated from HandleGenerator patterns
    _NODE_CONSTRAINTS = {
        NodeType.START: NodeConstraint(
            max_inputs=0,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},
            allowed_targets=None,  # Can connect to any node
        ),
        NodeType.ENDPOINT: NodeConstraint(
            max_inputs=None,
            max_outputs=0,
            required_handles={HandleLabel.DEFAULT},
            allowed_sources=None,  # Any node can connect
        ),
        NodeType.PERSON_JOB: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.FIRST, HandleLabel.DEFAULT},
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.CONDITION: NodeConstraint(
            max_inputs=1,  # Single input for condition evaluation
            max_outputs=None,  # Multiple branches allowed
            required_handles={HandleLabel.DEFAULT, HandleLabel.CONDTRUE, HandleLabel.CONDFALSE},
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.DB: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},  # Both input and output DEFAULT
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.CODE_JOB: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.API_JOB: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.USER_RESPONSE: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.HOOK: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.TEMPLATE_JOB: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.JSON_SCHEMA_VALIDATOR: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.TYPESCRIPT_AST: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.SUB_DIAGRAM: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},
            allowed_sources=None,
            allowed_targets=None,
        ),
        NodeType.INTEGRATED_API: NodeConstraint(
            max_inputs=None,
            max_outputs=None,
            required_handles={HandleLabel.DEFAULT},
            allowed_sources=None,
            allowed_targets=None,
        ),
    }

    # Execution constraints (unchanged from validation_rules.py)
    MAX_PARALLEL_NODES = 10
    MAX_RECURSION_DEPTH = 50
    MAX_TOTAL_NODES = 1000

    @classmethod
    def get_constraint(cls, node_type: NodeType) -> NodeConstraint:
        """Get constraints for a specific node type."""
        # Return constraint if defined, otherwise return default constraint
        return cls._NODE_CONSTRAINTS.get(
            node_type,
            NodeConstraint(
                max_inputs=None,
                max_outputs=None,
                required_handles={HandleLabel.DEFAULT},
                allowed_sources=None,
                allowed_targets=None,
            ),
        )

    @classmethod
    def get_required_handles(cls, node_type: NodeType) -> set[HandleLabel]:
        """Get required handles for a node type."""
        constraint = cls.get_constraint(node_type)
        return constraint.required_handles or set()

    @classmethod
    def get_max_inputs(cls, node_type: NodeType) -> int | None:
        """Get maximum allowed inputs for a node type."""
        constraint = cls.get_constraint(node_type)
        return constraint.max_inputs

    @classmethod
    def get_max_outputs(cls, node_type: NodeType) -> int | None:
        """Get maximum allowed outputs for a node type."""
        constraint = cls.get_constraint(node_type)
        return constraint.max_outputs

    @classmethod
    def can_connect(cls, source_type: NodeType, target_type: NodeType) -> bool:
        """Check if two node types can be connected."""
        source_constraint = cls.get_constraint(source_type)
        target_constraint = cls.get_constraint(target_type)

        # Check if source allows this target
        if (
            source_constraint.allowed_targets is not None
            and target_type not in source_constraint.allowed_targets
        ):
            return False

        # Check if target allows this source
        return not (
            target_constraint.allowed_sources is not None
            and source_type not in target_constraint.allowed_sources
        )

    # Backward compatibility: expose as dict-like interface
    NODE_CONNECTION_RULES = property(
        lambda self: {
            node_type: {
                "max_inputs": constraint.max_inputs,
                "max_outputs": constraint.max_outputs,
                "required_handles": list(constraint.required_handles)
                if constraint.required_handles
                else [],
                "allowed_sources": list(constraint.allowed_sources)
                if constraint.allowed_sources
                else None,
                "allowed_targets": list(constraint.allowed_targets)
                if constraint.allowed_targets
                else None,
            }
            for node_type, constraint in self._NODE_CONSTRAINTS.items()
        }
    )
