"""Unit tests for ExecutionRuleRegistry."""

from unittest.mock import Mock

import pytest

from dipeo.diagram_generated import NodeType
from dipeo.infrastructure.execution.rules import (
    BaseConnectionRule,
    BaseTransformRule,
    ExecutionRuleRegistry,
    RuleCategory,
    RuleKey,
    RulePriority,
)


class MockConnectionRule(BaseConnectionRule):
    """Mock connection rule for testing."""

    def __init__(self, name: str = "test_rule", allow_all: bool = True):
        super().__init__(name, "Test rule", RulePriority.NORMAL)
        self.allow_all = allow_all

    def can_connect(self, source_type: NodeType, target_type: NodeType) -> bool:
        return self.allow_all


class MockTransformRule(BaseTransformRule):
    """Mock transform rule for testing."""

    def __init__(self, name: str = "test_transform", transform_dict: dict | None = None):
        super().__init__(name, "Test transform", RulePriority.NORMAL)
        self.transform_dict = transform_dict or {}

    def applies_to(self, source, target):
        return True

    def get_transform(self, source, target):
        return self.transform_dict


class TestExecutionRuleRegistry:
    """Test ExecutionRuleRegistry functionality."""

    def test_create_registry(self):
        """Test creating a registry."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)
        assert registry is not None
        assert registry.list_rules() == []

    def test_register_connection_rule(self):
        """Test registering a connection rule."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)
        rule = MockConnectionRule("test_rule")
        key = RuleKey(
            name="test_rule",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.NORMAL,
        )

        registry.register_connection_rule(key, rule)

        rules = registry.list_rules(RuleCategory.CONNECTION)
        assert len(rules) == 1
        assert str(key) in rules

    def test_register_transform_rule(self):
        """Test registering a transform rule."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)
        rule = MockTransformRule("test_transform", {"test": True})
        key = RuleKey(
            name="test_transform",
            category=RuleCategory.TRANSFORM,
            priority=RulePriority.NORMAL,
        )

        registry.register_transform_rule(key, rule)

        rules = registry.list_rules(RuleCategory.TRANSFORM)
        assert len(rules) == 1
        assert str(key) in rules

    def test_can_connect_with_rules(self):
        """Test can_connect with registered rules."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)

        # Register a rule that blocks START as target
        rule = MockConnectionRule("no_start_target", allow_all=False)
        key = RuleKey(
            name="no_start_target",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.HIGH,
        )
        registry.register_connection_rule(key, rule)

        # Should block all connections
        assert not registry.can_connect(NodeType.PERSON_JOB, NodeType.START)

        # Register an allow-all rule with lower priority
        rule2 = MockConnectionRule("allow_all", allow_all=True)
        key2 = RuleKey(
            name="allow_all",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.LOW,
        )
        registry.register_connection_rule(key2, rule2)

        # High priority rule should still block
        assert not registry.can_connect(NodeType.PERSON_JOB, NodeType.START)

    def test_get_data_transform(self):
        """Test getting data transforms."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)

        # Register a transform rule
        rule = MockTransformRule("extract_tools", {"extract_tool_results": True})
        key = RuleKey(
            name="extract_tools",
            category=RuleCategory.TRANSFORM,
            priority=RulePriority.NORMAL,
        )
        registry.register_transform_rule(key, rule)

        # Use mock nodes
        source = Mock()
        target = Mock()

        transforms = registry.get_data_transform(source, target)
        assert transforms == {"extract_tool_results": True}

    def test_merge_transforms(self):
        """Test merging transforms."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)

        edge_transform = {"custom": "value", "priority": "edge"}
        type_transform = {"priority": "type", "default": "value"}

        merged = registry.merge_transforms(edge_transform, type_transform)

        # Edge transforms should take precedence
        assert merged["priority"] == "edge"
        assert merged["custom"] == "value"
        assert merged["default"] == "value"

    def test_rule_priority_ordering(self):
        """Test that rules are applied in priority order."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)

        # Register low priority rule first
        rule1 = MockTransformRule("low_priority", {"value": "low"})
        key1 = RuleKey(
            name="low_priority",
            category=RuleCategory.TRANSFORM,
            priority=RulePriority.LOW,
        )
        registry.register_transform_rule(key1, rule1)

        # Register high priority rule
        rule2 = MockTransformRule("high_priority", {"value": "high"})
        key2 = RuleKey(
            name="high_priority",
            category=RuleCategory.TRANSFORM,
            priority=RulePriority.HIGH,
        )
        registry.register_transform_rule(key2, rule2)

        # Use mock nodes
        source = Mock()
        target = Mock()

        # High priority rule should override low priority
        transforms = registry.get_data_transform(source, target)
        assert transforms["value"] == "high"

    def test_unregister_rule(self):
        """Test unregistering a rule."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)

        rule = MockConnectionRule("test_rule")
        key = RuleKey(
            name="test_rule",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.NORMAL,
        )
        registry.register_connection_rule(key, rule)

        assert len(registry.list_rules(RuleCategory.CONNECTION)) == 1

        registry.unregister(key)
        assert len(registry.list_rules(RuleCategory.CONNECTION)) == 0

    def test_immutable_rule_protection(self):
        """Test that immutable rules cannot be overridden."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)

        rule = MockConnectionRule("immutable_rule")
        key = RuleKey(
            name="immutable_rule",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.NORMAL,
            immutable=True,
        )
        registry.register_connection_rule(key, rule)

        # Try to register another rule with same key
        rule2 = MockConnectionRule("immutable_rule", allow_all=False)
        with pytest.raises(RuntimeError, match="Cannot override immutable rule"):
            registry.register_connection_rule(key, rule2, override=True)

    def test_freeze_registry(self):
        """Test freezing the registry."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)

        rule = MockConnectionRule("test_rule")
        key = RuleKey(
            name="test_rule",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.NORMAL,
        )
        registry.register_connection_rule(key, rule)

        registry.freeze()
        assert registry.is_frozen()

        # Try to override existing rule (should fail when frozen)
        rule2 = MockConnectionRule("test_rule", allow_all=False)
        with pytest.raises(RuntimeError, match="Registry is frozen"):
            registry.register_connection_rule(key, rule2, override=True)

    def test_temporary_override(self):
        """Test temporary rule override context manager."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)
        registry._environment = "testing"  # Enable temporary overrides

        rule = MockConnectionRule("test_rule", allow_all=True)
        key = RuleKey(
            name="test_rule",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.NORMAL,
        )
        registry.register_connection_rule(key, rule)

        # Original behavior
        assert registry.can_connect(NodeType.PERSON_JOB, NodeType.START)

        # Temporary override
        override_rule = MockConnectionRule("test_rule", allow_all=False)
        with registry.temporary_override({key: override_rule}):
            assert not registry.can_connect(NodeType.PERSON_JOB, NodeType.START)

        # Should be restored
        assert registry.can_connect(NodeType.PERSON_JOB, NodeType.START)

    def test_get_rule_info(self):
        """Test getting rule information."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)

        rule = MockConnectionRule("test_rule")
        key = RuleKey(
            name="test_rule",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.HIGH,
            description="Test description",
        )
        registry.register_connection_rule(key, rule)

        info = registry.get_rule_info(key)
        assert info is not None
        assert info["name"] == "test_rule"
        assert info["category"] == "connection"
        assert info["priority"] == "HIGH"
        assert info["description"] == "Test description"

    def test_connection_constraints(self):
        """Test getting connection constraints for a node type."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)

        # Register a simple rule
        rule = MockConnectionRule("simple", allow_all=True)
        key = RuleKey(
            name="simple",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.NORMAL,
        )
        registry.register_connection_rule(key, rule)

        constraints = registry.get_connection_constraints(NodeType.PERSON_JOB)

        assert "can_receive_from" in constraints
        assert "can_send_to" in constraints
        assert isinstance(constraints["can_receive_from"], list)
        assert isinstance(constraints["can_send_to"], list)

    def test_audit_trail(self):
        """Test audit trail recording."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=True)

        rule = MockConnectionRule("test_rule")
        key = RuleKey(
            name="test_rule",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.NORMAL,
        )
        registry.register_connection_rule(key, rule)

        trail = registry.get_audit_trail()
        assert len(trail) > 0

        last_record = trail[-1]
        assert last_record.rule_key == str(key)
        assert last_record.action == "register"
        assert last_record.success is True

    def test_override_without_permission(self):
        """Test that overriding without permission fails."""
        registry = ExecutionRuleRegistry(allow_override=False, enable_audit=False)

        rule = MockConnectionRule("test_rule")
        key = RuleKey(
            name="test_rule",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.NORMAL,
        )
        registry.register_connection_rule(key, rule)

        # Try to register another rule with same name
        rule2 = MockConnectionRule("test_rule", allow_all=False)
        with pytest.raises(RuntimeError, match="without override=True"):
            registry.register_connection_rule(key, rule2)

    def test_wrong_category_error(self):
        """Test that using wrong category raises error."""
        registry = ExecutionRuleRegistry(allow_override=True, enable_audit=False)

        rule = MockConnectionRule("test_rule")
        key = RuleKey(
            name="test_rule",
            category=RuleCategory.TRANSFORM,  # Wrong category for connection rule
            priority=RulePriority.NORMAL,
        )

        with pytest.raises(ValueError, match="category must be CONNECTION"):
            registry.register_connection_rule(key, rule)
