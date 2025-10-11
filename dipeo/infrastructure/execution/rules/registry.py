"""Execution rule registry for pluggable rule management."""

from __future__ import annotations

import threading
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar, cast

from dipeo.config import get_settings
from dipeo.diagram_generated import NodeType
from dipeo.diagram_generated.generated_nodes import ExecutableNode

from .base import (
    ConnectionRule,
    RuleCategory,
    RulePriority,
    TransformRule,
)

T = TypeVar("T")


@dataclass(frozen=True)
class RuleRegistrationRecord:
    """Audit record for rule registrations."""

    timestamp: datetime
    rule_key: str
    category: RuleCategory
    action: str  # 'register', 'override', 'unregister'
    caller_info: str
    environment: str
    success: bool
    error_message: str | None = None
    override_reason: str | None = None


@dataclass(frozen=True, slots=True)
class RuleKey:
    """Type-safe rule key with metadata."""

    name: str
    category: RuleCategory
    priority: RulePriority = RulePriority.NORMAL
    description: str = ""
    immutable: bool = False  # Cannot be overridden after registration
    dependencies: tuple[str, ...] = field(default_factory=tuple)

    def __str__(self) -> str:
        return f"{self.category.value}:{self.name}"

    def __repr__(self) -> str:
        return f"RuleKey[{self.category.value}:{self.name}] (priority={self.priority.name})"


class ExecutionRuleRegistry:
    """Thread-safe registry for execution rules with pluggability and safety features.

    Provides a centralized, extensible system for managing connection rules,
    transformation rules, and other execution rules. Supports dynamic registration,
    priority-based execution, and comprehensive audit trails.

    Example:
        # Create registry
        registry = ExecutionRuleRegistry()

        # Register a connection rule
        rule_key = RuleKey(
            name="start_no_input",
            category=RuleCategory.CONNECTION,
            priority=RulePriority.HIGH,
            description="START nodes cannot receive input"
        )
        registry.register_connection_rule(rule_key, my_rule)

        # Check connection
        can_connect = registry.can_connect(NodeType.PERSON_JOB, NodeType.START)

        # Register a transform rule
        rule_key = RuleKey(
            name="extract_tools",
            category=RuleCategory.TRANSFORM,
            priority=RulePriority.NORMAL,
            description="Extract tool results from PersonJob"
        )
        registry.register_transform_rule(rule_key, my_transform_rule)

        # Get transforms
        transforms = registry.get_data_transform(source_node, target_node)
    """

    def __init__(self, *, allow_override: bool | None = None, enable_audit: bool = True):
        """Initialize the rule registry.

        Args:
            allow_override: Whether to allow rule overrides. If None, determined by environment.
            enable_audit: Whether to enable audit trail logging.
        """

        settings = get_settings()
        env = settings.env.lower()

        # Storage for different rule types
        self._connection_rules: dict[str, ConnectionRule] = {}
        self._transform_rules: dict[str, TransformRule] = {}
        self._rule_keys: dict[str, RuleKey] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Audit trail
        self._audit_trail: list[RuleRegistrationRecord] = []
        self._enable_audit = enable_audit

        # Safety features
        self._frozen = False
        self._immutable_rules: set[str] = set()

        # Configuration
        self._environment = env
        if allow_override is not None:
            self._allow_override = allow_override
        else:
            self._allow_override = env in {"development", "dev", "testing", "test"}

        self._audit_max_records = 1000

    def register_connection_rule(
        self,
        key: RuleKey,
        rule: ConnectionRule,
        *,
        override: bool = False,
        override_reason: str | None = None,
    ) -> None:
        """Register a connection rule.

        Args:
            key: Rule key with metadata
            rule: Connection rule implementation
            override: Allow overriding existing rule
            override_reason: Reason for override (for audit)

        Raises:
            RuntimeError: If registration violates safety constraints
            ValueError: If invalid parameters provided
        """
        if key.category != RuleCategory.CONNECTION:
            raise ValueError(f"Rule key category must be CONNECTION, got {key.category.value}")

        caller_info = self._get_caller_info()

        with self._lock:
            exists = key.name in self._connection_rules

            # Check constraints
            self._check_registration_constraints(
                key, exists, override, override_reason, caller_info
            )

            # Store the rule
            self._connection_rules[key.name] = rule
            self._rule_keys[str(key)] = key

            if key.immutable:
                self._immutable_rules.add(str(key))

            # Record audit
            self._record_action(
                str(key),
                key.category,
                "override" if exists else "register",
                caller_info,
                True,
                override_reason=override_reason,
            )

    def register_transform_rule(
        self,
        key: RuleKey,
        rule: TransformRule,
        *,
        override: bool = False,
        override_reason: str | None = None,
    ) -> None:
        """Register a transform rule.

        Args:
            key: Rule key with metadata
            rule: Transform rule implementation
            override: Allow overriding existing rule
            override_reason: Reason for override (for audit)

        Raises:
            RuntimeError: If registration violates safety constraints
            ValueError: If invalid parameters provided
        """
        if key.category != RuleCategory.TRANSFORM:
            raise ValueError(f"Rule key category must be TRANSFORM, got {key.category.value}")

        caller_info = self._get_caller_info()

        with self._lock:
            exists = key.name in self._transform_rules

            # Check constraints
            self._check_registration_constraints(
                key, exists, override, override_reason, caller_info
            )

            # Store the rule
            self._transform_rules[key.name] = rule
            self._rule_keys[str(key)] = key

            if key.immutable:
                self._immutable_rules.add(str(key))

            # Record audit
            self._record_action(
                str(key),
                key.category,
                "override" if exists else "register",
                caller_info,
                True,
                override_reason=override_reason,
            )

    def can_connect(self, source_type: NodeType, target_type: NodeType) -> bool:
        """Check if connection between node types is allowed.

        Evaluates all registered connection rules in priority order.
        First rule that returns False blocks the connection.

        Args:
            source_type: Type of source node
            target_type: Type of target node

        Returns:
            True if connection is allowed by all rules, False otherwise
        """
        with self._lock:
            # Sort rules by priority (highest first)
            sorted_rules = sorted(
                self._connection_rules.items(),
                key=lambda x: self._get_rule_priority(x[0], RuleCategory.CONNECTION),
                reverse=True,
            )

            for _rule_name, rule in sorted_rules:
                if not rule.can_connect(source_type, target_type):
                    return False

            return True

    def get_connection_reason(self, source_type: NodeType, target_type: NodeType) -> str | None:
        """Get reason why connection is not allowed.

        Args:
            source_type: Type of source node
            target_type: Type of target node

        Returns:
            Reason string if not allowed, None if allowed
        """
        with self._lock:
            sorted_rules = sorted(
                self._connection_rules.items(),
                key=lambda x: self._get_rule_priority(x[0], RuleCategory.CONNECTION),
                reverse=True,
            )

            for _rule_name, rule in sorted_rules:
                if not rule.can_connect(source_type, target_type):
                    return rule.get_reason(source_type, target_type)

            return None

    def get_connection_constraints(self, node_type: NodeType) -> dict[str, list[NodeType]]:
        """Get connection constraints for a node type.

        Tests the node type against all other node types to determine
        valid sources and targets.

        Args:
            node_type: Type of node to check

        Returns:
            Dictionary with 'can_receive_from' and 'can_send_to' lists
        """
        all_types = list(NodeType)

        with self._lock:
            can_receive_from = [t for t in all_types if self.can_connect(t, node_type)]
            can_send_to = [t for t in all_types if self.can_connect(node_type, t)]

            return {
                "can_receive_from": can_receive_from,
                "can_send_to": can_send_to,
            }

    def get_data_transform(self, source: ExecutableNode, target: ExecutableNode) -> dict[str, Any]:
        """Get data transformation rules for node pair.

        Evaluates all applicable transform rules in priority order and merges
        their transformations. Higher priority rules override lower priority rules.

        Args:
            source: Source node
            target: Target node

        Returns:
            Dictionary of transformation rules to apply
        """
        with self._lock:
            # Get applicable rules sorted by priority
            applicable_rules = []
            for rule_name, rule in self._transform_rules.items():
                if rule.applies_to(source, target):
                    priority = self._get_rule_priority(rule_name, RuleCategory.TRANSFORM)
                    applicable_rules.append((priority, rule))

            # Sort by priority (lowest first, so higher priority overrides)
            applicable_rules.sort(key=lambda x: x[0])

            # Merge transforms
            result = {}
            for _priority, rule in applicable_rules:
                transforms = rule.get_transform(source, target)
                result.update(transforms)

            return result

    def merge_transforms(
        self, edge_transform: dict[str, Any], type_based_transform: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge edge-specific and type-based transformations.

        Edge-specific transforms take precedence over type-based transforms.

        Args:
            edge_transform: Edge-specific transformation rules
            type_based_transform: Type-based transformation rules

        Returns:
            Merged transformation dictionary
        """
        return {**type_based_transform, **edge_transform}

    def unregister(self, key: RuleKey, *, force: bool = False) -> None:
        """Unregister a rule.

        Args:
            key: Rule key to unregister
            force: Force unregistration even for protected rules

        Raises:
            RuntimeError: If attempting to unregister protected rule without force
        """
        caller_info = self._get_caller_info()

        with self._lock:
            key_str = str(key)

            # Check if rule exists
            exists = False
            if key.category == RuleCategory.CONNECTION:
                exists = key.name in self._connection_rules
            elif key.category == RuleCategory.TRANSFORM:
                exists = key.name in self._transform_rules

            if not exists:
                return

            # Check constraints
            stored_key = self._rule_keys.get(key_str)
            if stored_key and not force:
                if stored_key.immutable:
                    self._record_action(
                        key_str,
                        key.category,
                        "unregister_failed",
                        caller_info,
                        False,
                        error_message="Cannot unregister immutable rule without force=True",
                    )
                    raise RuntimeError(
                        f"Cannot unregister immutable rule '{key_str}' without force=True"
                    )

            # Remove the rule
            if key.category == RuleCategory.CONNECTION:
                self._connection_rules.pop(key.name, None)
            elif key.category == RuleCategory.TRANSFORM:
                self._transform_rules.pop(key.name, None)

            self._rule_keys.pop(key_str, None)
            self._immutable_rules.discard(key_str)

            # Record audit
            self._record_action(key_str, key.category, "unregister", caller_info, True)

    def list_rules(self, category: RuleCategory | None = None) -> list[str]:
        """List registered rules.

        Args:
            category: Filter by category. If None, returns all rules.

        Returns:
            List of rule key strings
        """
        with self._lock:
            if category is None:
                return list(self._rule_keys.keys())

            return [key_str for key_str, key in self._rule_keys.items() if key.category == category]

    def get_rule_info(self, key: RuleKey) -> dict[str, Any] | None:
        """Get information about a registered rule.

        Args:
            key: Rule key to query

        Returns:
            Rule information dictionary or None if not found
        """
        with self._lock:
            key_str = str(key)
            stored_key = self._rule_keys.get(key_str)

            if stored_key is None:
                return None

            rule = None
            if key.category == RuleCategory.CONNECTION:
                rule = self._connection_rules.get(key.name)
            elif key.category == RuleCategory.TRANSFORM:
                rule = self._transform_rules.get(key.name)

            return {
                "name": stored_key.name,
                "category": stored_key.category.value,
                "priority": stored_key.priority.name,
                "description": stored_key.description,
                "immutable": stored_key.immutable,
                "dependencies": list(stored_key.dependencies),
                "class": rule.__class__.__name__ if rule else "Unknown",
            }

    def freeze(self) -> None:
        """Freeze registry to prevent further modifications."""
        caller_info = self._get_caller_info()

        with self._lock:
            self._frozen = True
            self._record_action("*", RuleCategory.CONNECTION, "freeze", caller_info, True)

    def unfreeze(self, *, force: bool = False) -> None:
        """Unfreeze registry.

        Args:
            force: Force unfreezing even in production

        Raises:
            RuntimeError: If attempting to unfreeze in production without force
        """
        caller_info = self._get_caller_info()

        with self._lock:
            if self._environment == "production" and not force:
                self._record_action(
                    "*",
                    RuleCategory.CONNECTION,
                    "unfreeze_failed",
                    caller_info,
                    False,
                    error_message="Cannot unfreeze in production without force=True",
                )
                raise RuntimeError("Cannot unfreeze in production without force=True")

            self._frozen = False
            self._record_action("*", RuleCategory.CONNECTION, "unfreeze", caller_info, True)

    def is_frozen(self) -> bool:
        """Check if registry is frozen."""
        with self._lock:
            return self._frozen

    def get_audit_trail(self, rule_key: str | None = None) -> list[RuleRegistrationRecord]:
        """Get audit trail.

        Args:
            rule_key: Filter by rule key. If None, returns all records.

        Returns:
            List of registration records
        """
        with self._lock:
            if rule_key is None:
                return self._audit_trail.copy()
            return [record for record in self._audit_trail if record.rule_key == rule_key]

    @contextmanager
    def temporary_override(self, overrides: dict[RuleKey, ConnectionRule | TransformRule]):
        """Context manager for temporary rule overrides (testing only).

        Args:
            overrides: Dictionary of rule keys to temporary implementations

        Yields:
            None

        Raises:
            RuntimeError: If used in production environment
        """
        if self._environment == "production":
            raise RuntimeError("Temporary overrides not allowed in production")

        caller_info = self._get_caller_info()
        original_values: dict[RuleKey, Any] = {}

        # Store originals and apply overrides
        with self._lock:
            for key, rule in overrides.items():
                # Store original
                if key.category == RuleCategory.CONNECTION:
                    if key.name in self._connection_rules:
                        original_values[key] = ("connection", self._connection_rules[key.name])
                    else:
                        original_values[key] = None
                    self._connection_rules[key.name] = rule
                elif key.category == RuleCategory.TRANSFORM:
                    if key.name in self._transform_rules:
                        original_values[key] = ("transform", self._transform_rules[key.name])
                    else:
                        original_values[key] = None
                    self._transform_rules[key.name] = rule

                self._record_action(
                    str(key),
                    key.category,
                    "temp_override",
                    caller_info,
                    True,
                    override_reason="Temporary test override",
                )

        try:
            yield
        finally:
            # Restore originals
            with self._lock:
                for key, original in original_values.items():
                    if original is None:
                        # Rule didn't exist originally
                        if key.category == RuleCategory.CONNECTION:
                            self._connection_rules.pop(key.name, None)
                        elif key.category == RuleCategory.TRANSFORM:
                            self._transform_rules.pop(key.name, None)
                    else:
                        rule_type, original_rule = original
                        if rule_type == "connection":
                            self._connection_rules[key.name] = original_rule
                        elif rule_type == "transform":
                            self._transform_rules[key.name] = original_rule

                    self._record_action(
                        str(key),
                        key.category,
                        "temp_restore",
                        caller_info,
                        True,
                        override_reason="Restore after temporary override",
                    )

    def _get_rule_priority(self, rule_name: str, category: RuleCategory) -> int:
        """Get priority value for a rule."""
        key_str = f"{category.value}:{rule_name}"
        key = self._rule_keys.get(key_str)
        if key:
            return key.priority.value
        return RulePriority.NORMAL.value

    def _check_registration_constraints(
        self,
        key: RuleKey,
        exists: bool,
        override: bool,
        override_reason: str | None,
        caller_info: str,
    ) -> None:
        """Check all registration constraints."""
        key_str = str(key)

        # Check if frozen - when frozen, no new registrations or overrides allowed
        if self._frozen and exists:
            self._record_action(
                key_str,
                key.category,
                "register_failed",
                caller_info,
                False,
                error_message="Registry is frozen",
            )
            raise RuntimeError(f"Registry is frozen; refusing to rebind '{key_str}'")

        # Check immutable constraint
        if key_str in self._immutable_rules:
            self._record_action(
                key_str,
                key.category,
                "register_failed",
                caller_info,
                False,
                error_message="Cannot override immutable rule",
            )
            raise RuntimeError(f"Cannot override immutable rule '{key_str}'")

        # Check general override policy
        if exists and not (override or self._allow_override):
            self._record_action(
                key_str,
                key.category,
                "register_failed",
                caller_info,
                False,
                error_message="Override not allowed without explicit permission",
            )
            raise RuntimeError(
                f"Refusing to overwrite rule '{key_str}' without override=True "
                f"(env={self._environment}, allow_override={self._allow_override})"
            )

    def _record_action(
        self,
        rule_key: str,
        category: RuleCategory,
        action: str,
        caller_info: str,
        success: bool,
        *,
        error_message: str | None = None,
        override_reason: str | None = None,
    ) -> None:
        """Record an action in the audit trail."""
        if not self._enable_audit:
            return

        record = RuleRegistrationRecord(
            timestamp=datetime.now(),
            rule_key=rule_key,
            category=category,
            action=action,
            caller_info=caller_info,
            environment=self._environment,
            success=success,
            error_message=error_message,
            override_reason=override_reason,
        )

        # Keep audit trail bounded
        if len(self._audit_trail) > self._audit_max_records:
            keep_count = int(self._audit_max_records * 0.8)
            self._audit_trail = self._audit_trail[-keep_count:]

        self._audit_trail.append(record)

    @staticmethod
    def _get_caller_info() -> str:
        """Get caller information for audit trail."""
        import inspect

        try:
            frame = inspect.currentframe()
            if frame and frame.f_back and frame.f_back.f_back:
                caller_frame = frame.f_back.f_back
                filename = caller_frame.f_code.co_filename
                line_no = caller_frame.f_lineno
                func_name = caller_frame.f_code.co_name

                if "/DiPeO/" in filename:
                    filename = filename.split("/DiPeO/", 1)[1]

                return f"{filename}:{line_no} in {func_name}()"
        except (AttributeError, KeyError):
            pass

        return "unknown:0 in unknown()"
