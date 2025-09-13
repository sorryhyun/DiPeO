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

from dipeo.application.registry.service_registry import ServiceRegistry
from dipeo.diagram_generated.graphql_backups import operations

# Import result types for type checking
from dipeo.diagram_generated.graphql_backups.results import (
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

# Modules where resolvers live
RESOLVER_MODULES = [
    "dipeo.application.graphql.schema.query_resolvers",
    "dipeo.application.graphql.schema.mutations.api_key",
    "dipeo.application.graphql.schema.mutations.diagram",
    "dipeo.application.graphql.schema.mutations.execution",
    "dipeo.application.graphql.schema.mutations.node",
    "dipeo.application.graphql.schema.mutations.person",
    "dipeo.application.graphql.schema.mutations.upload",
    "dipeo.application.graphql.schema.mutations.cli_session",
    "dipeo.application.graphql.schema.subscription_resolvers",
]


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


def _import_modules(paths: list[str]):
    """Import resolver modules, ignoring import errors."""
    import logging

    logger = logging.getLogger(__name__)
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
    """
    Central executor for all GraphQL operations.

    Maps generated operation definitions to their resolver implementations,
    providing type-safe execution and validation.
    """

    def __init__(self, registry: ServiceRegistry):
        """
        Initialize the operation executor.

        Args:
            registry: Service registry for dependency injection
        """
        self.registry = registry
        self.operations: dict[str, OperationMapping] = {}
        self.subscriptions: dict[str, OperationMapping] = {}
        self._autowire()

    def _autowire(self) -> None:
        """Auto-wire operations to their resolvers based on naming conventions."""
        modules = _import_modules(RESOLVER_MODULES)

        # Map to store result types for specific operations
        result_type_map = {
            # API Key mutations
            "CreateApiKey": ApiKeyResult,
            "DeleteApiKey": DeleteResult,
            "TestApiKey": TestResult,
            # Diagram mutations
            "CreateDiagram": DiagramResult,
            "DeleteDiagram": DeleteResult,
            "ValidateDiagram": DiagramResult,
            # Execution mutations
            "ExecuteDiagram": ExecutionResult,
            "ControlExecution": ExecutionResult,
            "SendInteractiveResponse": ExecutionResult,
            "UpdateNodeState": ExecutionResult,
            # Node mutations
            "CreateNode": NodeResult,
            "UpdateNode": NodeResult,
            "DeleteNode": DeleteResult,
            # Person mutations
            "CreatePerson": PersonResult,
            "UpdatePerson": PersonResult,
            "DeletePerson": DeleteResult,
            # Upload mutations
            "UploadDiagram": DiagramResult,
            "UploadFile": FileOperationResult,
            "ConvertDiagramFormat": FileOperationResult,
            # CLI Session mutations
            "RegisterCliSession": CliSessionResult,
            "UnregisterCliSession": CliSessionResult,
        }

        for op_cls in _iter_operation_classes():
            func_name = _op_to_func_name(op_cls)
            found = False

            # Try to find the resolver function in the modules
            for m in modules:
                fn = getattr(m, func_name, None)
                if fn and (
                    inspect.iscoroutinefunction(fn)
                    or inspect.isfunction(fn)
                    or inspect.isasyncgenfunction(fn)
                ):
                    # Get result type if specified
                    op_name = op_cls.__name__.removesuffix("Operation")
                    result_type = result_type_map.get(op_name)

                    # Register the operation
                    self._register_operation(op_cls, fn, result_type)
                    found = True
                    break

            if not found:
                logger = logging.getLogger(__name__)
                logger.debug(
                    f"No resolver found for operation {op_cls.__name__}, expected function name: {func_name}"
                )

    def _register_operation(
        self, operation_class: type, resolver_method: Callable, result_type: type | None = None
    ):
        """
        Register an operation with its resolver.

        Args:
            operation_class: The generated operation class
            resolver_method: The resolver method to execute
            result_type: Expected result type (if applicable)
        """
        # Check if it's async (regular async function or async generator)
        is_async = inspect.iscoroutinefunction(resolver_method) or inspect.isasyncgenfunction(
            resolver_method
        )

        mapping = OperationMapping(
            operation_class=operation_class,
            resolver_method=resolver_method,
            result_type=result_type,
            is_async=is_async,
        )

        # Check if it's a subscription based on operation type
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
        """
        Execute a GraphQL operation by name.

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

        # Validate variables against operation schema
        validated_vars = self._validate_variables(mapping, variables or {})

        # Execute the resolver
        if mapping.is_async:
            result = await mapping.resolver_method(self.registry, **validated_vars)
        else:
            result = mapping.resolver_method(self.registry, **validated_vars)

        # Validate result type if specified
        if mapping.result_type:
            self._validate_result(result, mapping.result_type)

        # For queries, unwrap Result types to return data directly
        if mapping.operation_class.operation_type == "query" and hasattr(result, "data"):
            return result.data if result.data is not None else result

        return result

    async def execute_subscription(
        self,
        operation_name: str,
        variables: dict[str, Any] | None = None,
    ) -> AsyncGenerator[Any]:
        """
        Execute a GraphQL subscription by name.

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

        # Validate variables against subscription schema
        validated_vars = self._validate_variables(mapping, variables or {})

        # Execute the subscription resolver (should return an async generator)
        if mapping.is_async:
            async for item in mapping.resolver_method(self.registry, **validated_vars):
                yield item
        else:
            raise TypeError(f"Subscription '{operation_name}' resolver must be async generator")

    def _validate_variables(
        self, mapping: OperationMapping, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate and transform variables for an operation.

        Args:
            mapping: The operation mapping
            variables: Raw variables to validate

        Returns:
            Validated and transformed variables

        Raises:
            ValueError: If validation fails
        """
        operation_class = mapping.operation_class

        # Get expected variable types from the operation class
        if hasattr(operation_class, "Variables"):
            expected_vars = get_type_hints(operation_class.Variables)

            # Check for required variables
            for var_name, var_type in expected_vars.items():
                if var_name not in variables:
                    # Check if the type is Optional
                    if not self._is_optional_type(var_type):
                        raise ValueError(
                            f"Required variable '{var_name}' not provided for operation '{operation_class.operation_name}'"
                        )

            # Validate variable types (basic validation for now)
            validated = {}
            for var_name, var_value in variables.items():
                if var_name in expected_vars:
                    # Keep Strawberry input objects as-is (resolvers expect them)
                    # Only convert if it's not an input type
                    if hasattr(var_value, "__strawberry_definition__"):
                        # Check if it's an input type (has 'Input' in the class name)
                        if "Input" in var_value.__class__.__name__:
                            # Keep input objects as-is
                            validated[var_name] = var_value
                        else:
                            # Convert other Strawberry types to dicts
                            validated[var_name] = strawberry.asdict(var_value)
                    else:
                        validated[var_name] = var_value
                else:
                    # Ignore extra variables for flexibility
                    validated[var_name] = var_value

            return validated
        else:
            # No variable schema defined, pass through
            return variables

    def _validate_result(self, result: Any, expected_type: type) -> None:
        """
        Validate that a result matches the expected type.

        Args:
            result: The result to validate
            expected_type: The expected result type

        Raises:
            TypeError: If result doesn't match expected type
        """
        if not isinstance(result, expected_type):
            raise TypeError(
                f"Expected result of type {expected_type.__name__}, got {type(result).__name__}"
            )

    def _is_optional_type(self, type_hint: type) -> bool:
        """
        Check if a type hint is Optional.

        Args:
            type_hint: The type hint to check

        Returns:
            True if the type is Optional
        """
        # Check for Optional[T] which is Union[T, None]
        origin = getattr(type_hint, "__origin__", None)
        if origin is Union:
            args = getattr(type_hint, "__args__", ())
            return type(None) in args
        return False

    def get_operation_query(self, operation_name: str) -> str:
        """
        Get the GraphQL query string for an operation.

        Args:
            operation_name: Name of the operation

        Returns:
            The GraphQL query string

        Raises:
            ValueError: If operation not found
        """
        mapping = self.operations.get(operation_name)
        if not mapping:
            raise ValueError(f"Operation '{operation_name}' not found")

        return mapping.operation_class.query

    def list_operations(self) -> dict[str, dict[str, Any]]:
        """
        List all registered operations with their metadata.

        Returns:
            Dictionary of operation names to their metadata
        """
        operations_info = {}
        for name, mapping in self.operations.items():
            operations_info[name] = {
                "type": mapping.operation_class.operation_type,
                "query": mapping.operation_class.query,
                "has_variables": hasattr(mapping.operation_class, "Variables"),
                "result_type": mapping.result_type.__name__ if mapping.result_type else None,
                "is_async": mapping.is_async,
            }
        return operations_info

    def validate_all_operations_implemented(self) -> dict[str, bool]:
        """
        Check if all generated operations have implementations.

        Returns:
            Dictionary mapping operation names to implementation status
        """
        # Get all operation classes from the generated module
        all_operations = []
        for name in dir(operations):
            if name.endswith("Operation") and not name.startswith("_"):
                all_operations.append(name[: -len("Operation")])  # Remove 'Operation' suffix

        implementation_status = {}
        for op_name in all_operations:
            implementation_status[op_name] = op_name in self.operations

        return implementation_status
