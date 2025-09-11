"""
Operation Executor for mapping generated GraphQL operations to resolver implementations.

This module provides a unified interface for executing GraphQL operations using the
generated operation definitions from TypeScript query definitions.
"""

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional, Union, get_type_hints

import strawberry

from dipeo.application.registry.service_registry import ServiceRegistry
from dipeo.diagram_generated.graphql import operations

# Import all operation classes
from dipeo.diagram_generated.graphql.operations import (
    # Mutations
    ControlExecutionOperation,
    ConvertDiagramFormatOperation,
    CreateApiKeyOperation,
    CreateDiagramOperation,
    CreateNodeOperation,
    CreatePersonOperation,
    DeleteApiKeyOperation,
    DeleteDiagramOperation,
    DeleteNodeOperation,
    DeletePersonOperation,
    ExecuteDiagramOperation,
    # Subscriptions
    ExecutionUpdatesOperation,
    # Queries
    GetActiveCliSessionOperation,
    GetApiKeyOperation,
    GetApiKeysOperation,
    GetAvailableModelsOperation,
    GetDiagramOperation,
    GetExecutionCapabilitiesOperation,
    GetExecutionHistoryOperation,
    GetExecutionMetricsOperation,
    GetExecutionOperation,
    GetExecutionOrderOperation,
    GetOperationSchemaOperation,
    GetPersonOperation,
    GetPromptFileOperation,
    GetProviderOperationsOperation,
    GetProvidersOperation,
    GetSupportedFormatsOperation,
    GetSystemInfoOperation,
    HealthCheckOperation,
    ListConversationsOperation,
    ListDiagramsOperation,
    ListExecutionsOperation,
    ListPersonsOperation,
    ListPromptFilesOperation,
    RegisterCliSessionOperation,
    SendInteractiveResponseOperation,
    TestApiKeyOperation,
    UnregisterCliSessionOperation,
    UpdateNodeOperation,
    UpdateNodeStateOperation,
    UpdatePersonOperation,
    UploadDiagramOperation,
    UploadFileOperation,
    ValidateDiagramOperation,
)
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
        self._initialize_operation_mappings()

    def _initialize_operation_mappings(self):
        """Initialize mappings between operations and their resolver implementations."""
        # Import resolver modules dynamically to avoid circular imports
        from dipeo.application.graphql.schema.mutations import (
            api_key,
            cli_session,
            diagram,
            execution,
            node,
            person,
            upload,
        )
        from dipeo.application.graphql.schema.query_resolvers import (
            get_active_cli_session,
            get_api_key,
            get_api_keys,
            get_available_models,
            get_diagram,
            get_execution,
            get_execution_capabilities,
            get_execution_history,
            get_execution_metrics,
            get_execution_order,
            get_operation_schema,
            get_person,
            get_prompt_file,
            get_provider_operations,
            get_providers,
            get_supported_formats,
            get_system_info,
            health_check,
            list_conversations,
            list_diagrams,
            list_executions,
            list_persons,
            list_prompt_files,
        )

        # Map each operation to its resolver

        # Queries - 23 operations
        self._register_operation(GetDiagramOperation, get_diagram)
        self._register_operation(ListDiagramsOperation, list_diagrams)
        self._register_operation(GetExecutionOperation, get_execution)
        self._register_operation(ListExecutionsOperation, list_executions)
        self._register_operation(GetExecutionOrderOperation, get_execution_order)
        self._register_operation(GetExecutionMetricsOperation, get_execution_metrics)
        self._register_operation(GetExecutionHistoryOperation, get_execution_history)
        self._register_operation(GetExecutionCapabilitiesOperation, get_execution_capabilities)
        self._register_operation(GetPersonOperation, get_person)
        self._register_operation(ListPersonsOperation, list_persons)
        self._register_operation(GetApiKeyOperation, get_api_key)
        self._register_operation(GetApiKeysOperation, get_api_keys)
        self._register_operation(GetAvailableModelsOperation, get_available_models)
        self._register_operation(GetProvidersOperation, get_providers)
        self._register_operation(GetProviderOperationsOperation, get_provider_operations)
        self._register_operation(GetOperationSchemaOperation, get_operation_schema)
        self._register_operation(GetSystemInfoOperation, get_system_info)
        self._register_operation(HealthCheckOperation, health_check)
        self._register_operation(ListConversationsOperation, list_conversations)
        self._register_operation(GetSupportedFormatsOperation, get_supported_formats)
        self._register_operation(ListPromptFilesOperation, list_prompt_files)
        self._register_operation(GetPromptFileOperation, get_prompt_file)
        self._register_operation(GetActiveCliSessionOperation, get_active_cli_session)

        # Mutations - API Keys
        self._register_operation(CreateApiKeyOperation, api_key.create_api_key, ApiKeyResult)
        self._register_operation(DeleteApiKeyOperation, api_key.delete_api_key, DeleteResult)
        self._register_operation(TestApiKeyOperation, api_key.test_api_key, TestResult)

        # Mutations - Diagrams
        self._register_operation(CreateDiagramOperation, diagram.create_diagram, DiagramResult)
        self._register_operation(DeleteDiagramOperation, diagram.delete_diagram, DeleteResult)
        self._register_operation(ValidateDiagramOperation, diagram.validate_diagram, DiagramResult)

        # Mutations - Execution
        self._register_operation(
            ExecuteDiagramOperation, execution.execute_diagram, ExecutionResult
        )
        self._register_operation(
            ControlExecutionOperation, execution.control_execution, ExecutionResult
        )
        self._register_operation(
            SendInteractiveResponseOperation, execution.send_interactive_response, ExecutionResult
        )
        self._register_operation(
            UpdateNodeStateOperation, execution.update_node_state, ExecutionResult
        )

        # Mutations - Nodes
        self._register_operation(CreateNodeOperation, node.create_node, NodeResult)
        self._register_operation(UpdateNodeOperation, node.update_node, NodeResult)
        self._register_operation(DeleteNodeOperation, node.delete_node, DeleteResult)

        # Mutations - Persons
        self._register_operation(CreatePersonOperation, person.create_person, PersonResult)
        self._register_operation(UpdatePersonOperation, person.update_person, PersonResult)
        self._register_operation(DeletePersonOperation, person.delete_person, DeleteResult)

        # Mutations - Upload
        self._register_operation(UploadDiagramOperation, upload.upload_diagram, DiagramResult)
        self._register_operation(UploadFileOperation, upload.upload_file, FileOperationResult)
        self._register_operation(
            ConvertDiagramFormatOperation, upload.convert_diagram_format, FileOperationResult
        )

        # Mutations - CLI Session
        self._register_operation(
            RegisterCliSessionOperation, cli_session.register_cli_session, CliSessionResult
        )
        self._register_operation(
            UnregisterCliSessionOperation, cli_session.unregister_cli_session, CliSessionResult
        )

        # Queries - TODO: Query operations need standalone resolvers
        # Note: Queries module doesn't export standalone functions yet
        # All queries are currently implemented as methods on Query class
        # These need to be refactored to standalone functions like api_key mutations

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
        is_async = inspect.iscoroutinefunction(resolver_method)

        self.operations[operation_class.operation_name] = OperationMapping(
            operation_class=operation_class,
            resolver_method=resolver_method,
            result_type=result_type,
            is_async=is_async,
        )

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

        return result

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
                    # Convert Strawberry objects to dicts if needed
                    if hasattr(var_value, "__strawberry_definition__"):
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
