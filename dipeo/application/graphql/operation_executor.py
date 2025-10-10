"""
Operation Executor for mapping generated GraphQL operations to resolver implementations.

This module provides a unified interface for executing GraphQL operations using the
generated operation definitions from TypeScript query definitions.
"""

import inspect
import logging
import re
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Optional, Union, get_type_hints

import strawberry

from dipeo.application.registry.enhanced_service_registry import (
    EnhancedServiceRegistry as ServiceRegistry,
)
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.graphql import operations

# Import result types for type checking
from dipeo.diagram_generated.graphql.results import (
    ApiKeyResult,
    CliSessionResult,
    DeleteResult,
    DiagramResult,
    ExecutionResult,
    FileOperationResult,
    NodeResult,
    PersonResult,
    TestResult,
)

# Modules where resolvers live (cached at module load time)
_RESOLVER_MODULES_CACHE = None


def _get_resolver_modules():
    """Get cached resolver modules (import only once)."""
    global _RESOLVER_MODULES_CACHE
    if _RESOLVER_MODULES_CACHE is None:
        _RESOLVER_MODULES_CACHE = _import_modules(
            [
                "dipeo.application.graphql.schema.query_resolvers",
                "dipeo.application.graphql.schema.mutations.api_key",
                "dipeo.application.graphql.schema.mutations.diagram",
                "dipeo.application.graphql.schema.mutations.execution",
                "dipeo.application.graphql.schema.mutations.node",
                "dipeo.application.graphql.schema.mutations.person",
                "dipeo.application.graphql.schema.mutations.upload",
                "dipeo.application.graphql.schema.mutations.cli_session",
                "dipeo.application.graphql.schema.mutations.provider",
                "dipeo.application.graphql.schema.subscription_resolvers",
            ]
        )
    return _RESOLVER_MODULES_CACHE


def _camel_to_snake(s: str) -> str:
    """Convert CamelCase to snake_case."""
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def _op_to_func_name(op_cls: type) -> str:
    """Convert operation class name to expected function name.

    Example: GetDiagramOperation -> get_diagram
    """
    return _camel_to_snake(op_cls.__name__.removesuffix("Operation"))


def _iter_operation_classes():
    """Iterate over all operation classes from the generated module."""
    for name in dir(operations):
        if name.endswith("Operation") and not name.startswith("_"):
            yield getattr(operations, name)


logger = get_module_logger(__name__)


def _import_modules(paths: list[str]):
    """Import resolver modules, ignoring import errors."""
    out = []
    for p in paths:
        try:
            module = import_module(p)
            out.append(module)
        except Exception as e:
            logger.debug(f"Failed to import module {p}: {e}")
    return out


@dataclass
class OperationMapping:
    """Mapping between an operation and its resolver implementation."""

    operation_class: type
    resolver_method: Callable
    result_type: type | None = None
    is_async: bool = True


class OperationExecutor:
    """Central executor for all GraphQL operations.

    Maps generated operation definitions to resolver implementations with type-safe execution.
    """

    def __init__(self, registry: ServiceRegistry):
        """Initialize the operation executor with service registry."""
        self.registry = registry
        self.operations: dict[str, OperationMapping] = {}
        self.subscriptions: dict[str, OperationMapping] = {}
        self._autowire()

    def _resolve_result_type(self, op_name: str) -> type | None:
        """Resolve result type by convention.

        Args:
            op_name: Operation name (e.g., "GetExecution", "CreateDiagram")

        Returns:
            The result type if found, None otherwise
        """
        # Map specific operations to their result types
        specific_mappings = {
            "ExecuteDiagram": "ExecutionResult",
            "ControlExecution": "ExecutionResult",
            "SendInteractiveResponse": "ExecutionResult",
            "UpdateNodeState": "ExecutionResult",
            "UploadFile": "FileOperationResult",
            "ConvertDiagramFormat": "FileOperationResult",
        }

        # Determine candidate result type name
        if op_name in specific_mappings:
            candidate = specific_mappings[op_name]
        elif op_name.startswith("Delete"):
            candidate = "DeleteResult"
        elif op_name.startswith("Test"):
            candidate = "TestResult"
        else:
            # Strip common prefixes to get base entity name
            prefixes = [
                "Get",
                "List",
                "Create",
                "Update",
                "Register",
                "Unregister",
                "Upload",
                "Convert",
                "Validate",
            ]
            base = op_name
            for prefix in prefixes:
                if op_name.startswith(prefix):
                    base = op_name[len(prefix) :]
                    break
            candidate = f"{base}Result"

        # Try to import the result type
        try:
            results_mod = import_module("dipeo.diagram_generated.graphql.results")
            return getattr(results_mod, candidate, None)
        except Exception as e:
            logger.debug(f"Could not resolve result type for {op_name}: {e}")
            return None

    def _autowire(self) -> None:
        """Auto-wire operations to their resolvers based on naming conventions."""
        modules = _get_resolver_modules()

        # Operations that intentionally don't have resolvers (base classes, not yet implemented, etc.)
        expected_missing = {
            "BaseGraphQLOperation",
            "GetSupportedFormatsOperation",
        }

        for op_cls in _iter_operation_classes():
            func_name = _op_to_func_name(op_cls)

            # Try to find the resolver function in the modules
            for m in modules:
                fn = getattr(m, func_name, None)
                if fn and (
                    inspect.iscoroutinefunction(fn)
                    or inspect.isfunction(fn)
                    or inspect.isasyncgenfunction(fn)
                ):
                    # Get result type using convention-based resolution
                    op_name = op_cls.__name__.removesuffix("Operation")
                    result_type = self._resolve_result_type(op_name)

                    # Register the operation
                    self._register_operation(op_cls, fn, result_type)
                    break
            else:
                pass

    def _register_operation(
        self, operation_class: type, resolver_method: Callable, result_type: type | None = None
    ):
        """Register an operation with its resolver.

        Args:
            operation_class: The generated operation class
            resolver_method: The resolver method to execute
            result_type: Expected result type (if applicable)
        """
        is_async = inspect.iscoroutinefunction(resolver_method) or inspect.isasyncgenfunction(
            resolver_method
        )
        mapping = OperationMapping(
            operation_class=operation_class,
            resolver_method=resolver_method,
            result_type=result_type,
            is_async=is_async,
        )

        # Register as subscription or regular operation
        if getattr(operation_class, "operation_type", None) == "subscription":
            self.subscriptions[operation_class.operation_name] = mapping
        else:
            self.operations[operation_class.operation_name] = mapping

    async def execute(
        self,
        operation_name: str,
        variables: dict[str, Any] | None = None,
        info: Any | None = None,
    ) -> Any:
        """Execute a GraphQL operation by name.

        Args:
            operation_name: Name of the operation to execute
            variables: Variables for the operation
            info: GraphQL info context (if available)

        Returns:
            The result of the operation

        Raises:
            ValueError: If operation is not found or validation fails
        """
        mapping = self.operations.get(operation_name)
        if not mapping:
            raise ValueError(
                f"Operation '{operation_name}' not found. Available operations: {list(self.operations.keys())}"
            )

        # Validate variables and execute
        validated_vars = self._validate_variables(mapping, variables or {})
        result = (
            await mapping.resolver_method(self.registry, **validated_vars)
            if mapping.is_async
            else mapping.resolver_method(self.registry, **validated_vars)
        )

        # Validate mutations return correct Result types
        if mapping.result_type and mapping.operation_class.operation_type == "mutation":
            self._validate_result(result, mapping.result_type)

        # Unwrap queries that accidentally return Result types
        if mapping.operation_class.operation_type == "query" and hasattr(result, "data"):
            return result.data if result.data is not None else result

        return result

    async def execute_subscription(
        self,
        operation_name: str,
        variables: dict[str, Any] | None = None,
    ) -> AsyncGenerator[Any]:
        """Execute a GraphQL subscription by name.

        Args:
            operation_name: Name of the subscription to execute
            variables: Variables for the subscription

        Yields:
            Subscription events

        Raises:
            ValueError: If subscription is not found or validation fails
        """
        mapping = self.subscriptions.get(operation_name)
        if not mapping:
            raise ValueError(
                f"Subscription '{operation_name}' not found. Available subscriptions: {list(self.subscriptions.keys())}"
            )

        if not mapping.is_async:
            raise TypeError(f"Subscription '{operation_name}' resolver must be async generator")

        validated_vars = self._validate_variables(mapping, variables or {})
        async for item in mapping.resolver_method(self.registry, **validated_vars):
            yield item

    def _validate_variables(
        self, mapping: OperationMapping, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate and transform variables for an operation.

        Args:
            mapping: The operation mapping
            variables: Raw variables to validate

        Returns:
            Validated and transformed variables

        Raises:
            ValueError: If validation fails
        """
        operation_class = mapping.operation_class

        # No variable schema defined, pass through
        if not hasattr(operation_class, "Variables"):
            return variables

        expected_vars = get_type_hints(operation_class.Variables)

        # Check for required variables
        for var_name, var_type in expected_vars.items():
            if var_name not in variables and not self._is_optional_type(var_type):
                raise ValueError(
                    f"Required variable '{var_name}' not provided for operation '{operation_class.operation_name}'"
                )

        # Transform variables (keep Strawberry Input objects, convert other types)
        validated = {}
        for var_name, var_value in variables.items():
            # Keep Strawberry input objects as-is, convert other Strawberry types to dicts
            if (
                hasattr(var_value, "__strawberry_definition__")
                and "Input" not in var_value.__class__.__name__
            ):
                validated[var_name] = strawberry.asdict(var_value)
            else:
                validated[var_name] = var_value

        return validated

    def _validate_result(self, result: Any, expected_type: type) -> None:
        """Validate that a result matches the expected type."""
        if not isinstance(result, expected_type):
            raise TypeError(
                f"Expected result of type {expected_type.__name__}, got {type(result).__name__}"
            )

    def _is_optional_type(self, type_hint: type) -> bool:
        """Check if a type hint is Optional (Union[T, None])."""
        origin = getattr(type_hint, "__origin__", None)
        return origin is Union and type(None) in getattr(type_hint, "__args__", ())

    def get_operation_query(self, operation_name: str) -> str:
        """Get the GraphQL query string for an operation."""
        mapping = self.operations.get(operation_name)
        if not mapping:
            raise ValueError(f"Operation '{operation_name}' not found")
        return mapping.operation_class.query

    def list_operations(self) -> dict[str, dict[str, Any]]:
        """List all registered operations with their metadata."""
        return {
            name: {
                "type": mapping.operation_class.operation_type,
                "query": mapping.operation_class.query,
                "has_variables": hasattr(mapping.operation_class, "Variables"),
                "result_type": mapping.result_type.__name__ if mapping.result_type else None,
                "is_async": mapping.is_async,
            }
            for name, mapping in self.operations.items()
        }

    def validate_all_operations_implemented(self) -> dict[str, bool]:
        """Check if all generated operations have implementations."""
        all_operations = [
            name[: -len("Operation")]
            for name in dir(operations)
            if name.endswith("Operation") and not name.startswith("_")
        ]
        return {op_name: op_name in self.operations for op_name in all_operations}
