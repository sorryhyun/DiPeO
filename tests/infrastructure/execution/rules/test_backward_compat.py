"""Tests for backward compatibility layer."""

from unittest.mock import Mock

import pytest

from dipeo.diagram_generated import NodeType
from dipeo.diagram_generated.generated_nodes import PersonJobNode
from dipeo.domain.execution.rules import DataTransformRules, NodeConnectionRules
from dipeo.infrastructure.execution.rules.compat import reset_default_registry


class TestNodeConnectionRulesBackwardCompat:
    """Test backward compatibility of NodeConnectionRules."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_default_registry()

    def test_can_connect_start_no_input(self):
        """Test that START nodes cannot receive input."""
        # Any node -> START should be False
        assert not NodeConnectionRules.can_connect(NodeType.PERSON_JOB, NodeType.START)
        assert not NodeConnectionRules.can_connect(NodeType.CODE_JOB, NodeType.START)
        assert not NodeConnectionRules.can_connect(NodeType.ENDPOINT, NodeType.START)

    def test_can_connect_endpoint_no_output(self):
        """Test that ENDPOINT nodes cannot send output."""
        # ENDPOINT -> any node should be False
        assert not NodeConnectionRules.can_connect(NodeType.ENDPOINT, NodeType.PERSON_JOB)
        assert not NodeConnectionRules.can_connect(NodeType.ENDPOINT, NodeType.CODE_JOB)
        assert not NodeConnectionRules.can_connect(NodeType.ENDPOINT, NodeType.START)

    def test_can_connect_valid_connections(self):
        """Test valid connections."""
        # START -> other nodes
        assert NodeConnectionRules.can_connect(NodeType.START, NodeType.PERSON_JOB)
        assert NodeConnectionRules.can_connect(NodeType.START, NodeType.CODE_JOB)
        assert NodeConnectionRules.can_connect(NodeType.START, NodeType.ENDPOINT)

        # Normal nodes -> other nodes (except START)
        assert NodeConnectionRules.can_connect(NodeType.PERSON_JOB, NodeType.CODE_JOB)
        assert NodeConnectionRules.can_connect(NodeType.CODE_JOB, NodeType.PERSON_JOB)
        assert NodeConnectionRules.can_connect(NodeType.PERSON_JOB, NodeType.ENDPOINT)

    def test_can_connect_output_capable_nodes(self):
        """Test output-capable node connections."""
        output_capable = [
            NodeType.PERSON_JOB,
            NodeType.CONDITION,
            NodeType.CODE_JOB,
            NodeType.API_JOB,
            NodeType.START,
        ]

        for node_type in output_capable:
            # Should be able to connect to non-START nodes
            assert NodeConnectionRules.can_connect(node_type, NodeType.PERSON_JOB)
            assert NodeConnectionRules.can_connect(node_type, NodeType.ENDPOINT)

            # Should NOT be able to connect to START
            assert not NodeConnectionRules.can_connect(node_type, NodeType.START)

    def test_get_connection_constraints_start(self):
        """Test connection constraints for START node."""
        constraints = NodeConnectionRules.get_connection_constraints(NodeType.START)

        # START cannot receive from anyone
        assert constraints["can_receive_from"] == []

        # START can send to everyone except itself
        assert NodeType.START not in constraints["can_send_to"]
        assert NodeType.PERSON_JOB in constraints["can_send_to"]
        assert NodeType.ENDPOINT in constraints["can_send_to"]

    def test_get_connection_constraints_endpoint(self):
        """Test connection constraints for ENDPOINT node."""
        constraints = NodeConnectionRules.get_connection_constraints(NodeType.ENDPOINT)

        # ENDPOINT cannot send to anyone
        assert constraints["can_send_to"] == []

        # ENDPOINT can receive from everyone except itself
        assert NodeType.ENDPOINT not in constraints["can_receive_from"]
        assert NodeType.PERSON_JOB in constraints["can_receive_from"]
        assert NodeType.START in constraints["can_receive_from"]

    def test_get_connection_constraints_regular_node(self):
        """Test connection constraints for regular nodes."""
        constraints = NodeConnectionRules.get_connection_constraints(NodeType.PERSON_JOB)

        # Can receive from non-ENDPOINT nodes
        assert NodeType.START in constraints["can_receive_from"]
        assert NodeType.CODE_JOB in constraints["can_receive_from"]
        assert NodeType.ENDPOINT not in constraints["can_receive_from"]

        # Can send to non-START nodes
        assert NodeType.ENDPOINT in constraints["can_send_to"]
        assert NodeType.CODE_JOB in constraints["can_send_to"]
        assert NodeType.START not in constraints["can_send_to"]

    def test_get_registry(self):
        """Test accessing the underlying registry."""
        registry = NodeConnectionRules.get_registry()
        assert registry is not None

        # Should be able to use registry methods
        rules = registry.list_rules()
        assert len(rules) > 0


class TestDataTransformRulesBackwardCompat:
    """Test backward compatibility of DataTransformRules."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_default_registry()

    def test_get_data_transform_personjob_with_tools(self):
        """Test transform rule for PersonJob with tools."""
        # Use mock with tools attribute
        source = Mock(spec=PersonJobNode)
        source.tools = ["calculator", "web_search"]
        target = Mock()

        transforms = DataTransformRules.get_data_transform(source, target)
        assert transforms.get("extract_tool_results") is True

    def test_get_data_transform_personjob_without_tools(self):
        """Test transform rule for PersonJob without tools."""
        # Use mock without tools
        source = Mock(spec=PersonJobNode)
        source.tools = None
        target = Mock()

        transforms = DataTransformRules.get_data_transform(source, target)
        assert "extract_tool_results" not in transforms

    def test_get_data_transform_non_personjob(self):
        """Test transform rule for non-PersonJob nodes."""
        # Use simple mocks (not PersonJob)
        source = Mock()
        target = Mock()

        transforms = DataTransformRules.get_data_transform(source, target)
        assert "extract_tool_results" not in transforms

    def test_merge_transforms_edge_priority(self):
        """Test that edge transforms have priority over type transforms."""
        edge_transform = {"custom": "edge_value", "priority": "edge"}
        type_transform = {"priority": "type", "default": "type_value"}

        merged = DataTransformRules.merge_transforms(edge_transform, type_transform)

        # Edge values should take precedence
        assert merged["priority"] == "edge"
        assert merged["custom"] == "edge_value"
        assert merged["default"] == "type_value"

    def test_merge_transforms_empty_dicts(self):
        """Test merging empty transform dictionaries."""
        merged = DataTransformRules.merge_transforms({}, {})
        assert merged == {}

        merged = DataTransformRules.merge_transforms({"key": "value"}, {})
        assert merged == {"key": "value"}

        merged = DataTransformRules.merge_transforms({}, {"key": "value"})
        assert merged == {"key": "value"}

    def test_get_registry(self):
        """Test accessing the underlying registry."""
        registry = DataTransformRules.get_registry()
        assert registry is not None

        # Should be able to use registry methods
        rules = registry.list_rules()
        assert len(rules) > 0


class TestRegistryExtensibility:
    """Test that the registry can be extended with custom rules."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_default_registry()

    def test_register_custom_connection_rule(self):
        """Test registering a custom connection rule."""
        from dipeo.infrastructure.execution.rules import (
            BaseConnectionRule,
            RuleCategory,
            RuleKey,
            RulePriority,
        )

        class CustomRule(BaseConnectionRule):
            def __init__(self):
                super().__init__("custom_rule", "Custom test rule", RulePriority.HIGH)

            def can_connect(self, source_type, target_type):
                # Block all CODE_JOB to CODE_JOB connections
                return not (source_type == NodeType.CODE_JOB and target_type == NodeType.CODE_JOB)

        registry = NodeConnectionRules.get_registry()
        rule = CustomRule()
        key = RuleKey(
            name=rule.name,
            category=RuleCategory.CONNECTION,
            priority=rule.priority,
        )
        registry.register_connection_rule(key, rule)

        # Custom rule should be enforced
        assert not NodeConnectionRules.can_connect(NodeType.CODE_JOB, NodeType.CODE_JOB)
        # Other connections should still work
        assert NodeConnectionRules.can_connect(NodeType.CODE_JOB, NodeType.PERSON_JOB)

    def test_register_custom_transform_rule(self):
        """Test registering a custom transform rule."""
        from dipeo.diagram_generated.generated_nodes import CodeJobNode
        from dipeo.infrastructure.execution.rules import (
            BaseTransformRule,
            RuleCategory,
            RuleKey,
            RulePriority,
        )

        class CustomTransformRule(BaseTransformRule):
            def __init__(self):
                super().__init__("custom_transform", "Custom transform", RulePriority.HIGH)

            def applies_to(self, source, target):
                return isinstance(source, CodeJobNode)

            def get_transform(self, source, target):
                return {"custom_transform": "applied"}

        registry = DataTransformRules.get_registry()
        rule = CustomTransformRule()
        key = RuleKey(
            name=rule.name,
            category=RuleCategory.TRANSFORM,
            priority=rule.priority,
        )
        registry.register_transform_rule(key, rule)

        # Custom rule should be applied - use mocks
        source = Mock(spec=CodeJobNode)
        target = Mock(spec=CodeJobNode)

        transforms = DataTransformRules.get_data_transform(source, target)
        assert transforms.get("custom_transform") == "applied"
