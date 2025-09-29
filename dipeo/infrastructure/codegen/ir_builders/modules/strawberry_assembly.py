"""Strawberry IR assembly module."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from dipeo.domain.codegen.ir_builder_port import IRData, IRMetadata
from dipeo.infrastructure.codegen.ir_builders.core import (
    BuildContext,
    BuildStep,
    StepResult,
    StepType,
)

logger = logging.getLogger(__name__)


class BuildDomainIRStep(BuildStep):
    """Step to build domain IR data structure."""

    def __init__(self):
        """Initialize domain IR builder step."""
        super().__init__(
            name="build_domain_ir",
            step_type=StepType.TRANSFORM,
            required=True
        )
        self.add_dependency("extract_domain_models")

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Build domain IR data structure.

        Args:
            context: Build context
            input_data: Dictionary with domain data from extraction step

        Returns:
            StepResult with domain IR data
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_domain_models" in input_data:
            domain_data = input_data["extract_domain_models"]
        else:
            return StepResult(success=False, error="Expected domain models data as input")

        # Extract components from domain data
        domain_types = domain_data.get("models", [])
        interfaces = domain_data.get("interfaces", [])
        enums = domain_data.get("enums", [])
        scalars = domain_data.get("scalars", [])
        graphql_inputs = domain_data.get("inputs", [])

        domain_ir = self._build_domain_ir(
            domain_types, interfaces, enums, scalars, graphql_inputs
        )

        return StepResult(
            success=True,
            data=domain_ir,
            metadata={
                "type_count": len(domain_ir["types"]),
                "interface_count": len(domain_ir["interfaces"]),
                "enum_count": len(domain_ir["enums"]),
            }
        )

    def _build_domain_ir(
        self,
        domain_types: list[dict[str, Any]],
        interfaces: list[dict[str, Any]],
        enums: list[dict[str, Any]],
        scalars: list[dict[str, Any]] | None = None,
        graphql_inputs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Build domain IR data structure.

        Args:
            domain_types: List of domain type definitions
            interfaces: List of interface definitions
            enums: List of enum definitions
            scalars: List of scalar definitions
            graphql_inputs: List of GraphQL input type definitions

        Returns:
            Domain IR data dictionary
        """
        # Filter and organize types
        organized_types = self._organize_domain_types(domain_types)
        organized_interfaces = self._organize_interfaces(interfaces)

        # The legacy builder exposes scalars/inputs even when empty, so mirror that API.
        domain_data = {
            "types": organized_types,
            "interfaces": organized_interfaces,
            "enums": enums,
            "scalars": scalars or [],
            "inputs": graphql_inputs or [],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "type_count": len(organized_types),
                "interface_count": len(organized_interfaces),
                "enum_count": len(enums),
            },
        }
        return domain_data

    def _organize_domain_types(self, domain_types: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Organize and validate domain types.

        Args:
            domain_types: List of domain type definitions

        Returns:
            Organized list of domain types
        """
        organized = []
        seen_names = set()

        for dtype in domain_types:
            name = dtype.get("name", "")
            if not name:
                continue

            if name in seen_names:
                continue

            seen_names.add(name)
            organized.append(dtype)

        return organized

    def _organize_interfaces(self, interfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Organize and filter interfaces.

        Args:
            interfaces: List of interface definitions

        Returns:
            Organized list of interfaces
        """
        organized = []
        seen_names = set()

        for interface in interfaces:
            name = interface.get("name", "")
            if not name:
                continue

            # Skip internal interfaces
            if name.startswith("_") or name.endswith("Internal"):
                continue

            if name in seen_names:
                continue

            seen_names.add(name)
            organized.append(interface)

        return organized


class BuildOperationsIRStep(BuildStep):
    """Step to build operations IR data structure."""

    def __init__(self):
        """Initialize operations IR builder step."""
        super().__init__(
            name="build_operations_ir",
            step_type=StepType.TRANSFORM,
            required=True
        )
        self.add_dependency("extract_graphql_operations")

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Build operations IR data structure.

        Args:
            context: Build context
            input_data: Dictionary with operations data from extraction step

        Returns:
            StepResult with operations IR data
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_graphql_operations" in input_data:
            operations_data = input_data["extract_graphql_operations"]
        else:
            return StepResult(success=False, error="Expected GraphQL operations data as input")

        # Extract components from operations data
        operations = operations_data.get("operations", [])
        input_types = operations_data.get("input_types", [])
        result_types = operations_data.get("result_types", [])

        operations_ir = self._build_operations_ir(operations, input_types, result_types)

        return StepResult(
            success=True,
            data=operations_ir,
            metadata={
                "total_operations": operations_ir["metadata"]["total_count"],
                "query_count": operations_ir["metadata"]["query_count"],
                "mutation_count": operations_ir["metadata"]["mutation_count"],
                "subscription_count": operations_ir["metadata"]["subscription_count"],
            }
        )

    def _build_operations_ir(
        self,
        operations: list[dict[str, Any]],
        input_types: list[dict[str, Any]],
        result_types: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build operations IR data structure.

        Args:
            operations: List of operation definitions
            input_types: List of input type definitions
            result_types: List of result type definitions

        Returns:
            Operations IR data dictionary
        """
        # Organize operations by type
        queries = []
        mutations = []
        subscriptions = []

        for op in operations:
            op_type = op.get("type", "query").lower()
            if op_type == "subscription":
                subscriptions.append(op)
            elif op_type == "mutation":
                mutations.append(op)
            else:
                queries.append(op)

        operations_data = {
            "queries": queries,
            "mutations": mutations,
            "subscriptions": subscriptions,
            "input_types": input_types,
            "result_types": result_types,
            "metadata": {
                "query_count": len(queries),
                "mutation_count": len(mutations),
                "subscription_count": len(subscriptions),
                "total_count": len(operations),
                "total_queries": len(queries),
                "total_mutations": len(mutations),
                "total_subscriptions": len(subscriptions),
            },
            "raw_queries": queries,
            "raw_mutations": mutations,
            "raw_subscriptions": subscriptions,
        }

        return operations_data


class BuildCompleteIRStep(BuildStep):
    """Step to build complete IR data structure."""

    def __init__(self):
        """Initialize complete IR builder step."""
        super().__init__(
            name="build_complete_ir",
            step_type=StepType.ASSEMBLE,
            required=True
        )
        self.add_dependency("build_operations_ir")
        self.add_dependency("build_domain_ir")

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Build complete IR data structure.

        Args:
            context: Build context
            input_data: Dictionary with operations and domain data from previous steps

        Returns:
            StepResult with complete IRData instance
        """
        # Handle input from dependencies
        if not isinstance(input_data, dict):
            return StepResult(success=False, error="Expected dictionary input with step data")

        operations_data = input_data.get("build_operations_ir")
        domain_data = input_data.get("build_domain_ir")

        if not operations_data:
            return StepResult(success=False, error="Missing operations IR data")
        if not domain_data:
            return StepResult(success=False, error="Missing domain IR data")

        # Get optional data from context
        config = context.config.get("strawberry", {})
        source_files = context.get_metadata("source_files", [])
        node_specs = context.get_step_data("extract_node_specs", [])

        complete_ir = self._build_complete_ir(
            operations_data, domain_data, config, source_files, node_specs
        )

        return StepResult(
            success=True,
            data=complete_ir,
            metadata={
                "total_operations": complete_ir.data["metadata"]["total_operations"],
                "interface_count": complete_ir.data["metadata"]["interface_count"],
                "enum_count": complete_ir.data["metadata"]["enum_count"],
            }
        )

    def _build_complete_ir(
        self,
        operations_data: dict[str, Any],
        domain_data: dict[str, Any],
        config: dict[str, Any],
        source_files: Optional[list[str]] = None,
        node_specs: Optional[list[dict[str, Any]]] = None,
    ) -> IRData:
        """Build complete IR data structure.

        Args:
            operations_data: Operations IR data
            domain_data: Domain IR data
            config: Configuration data
            source_files: List of source files
            node_specs: List of node specifications

        Returns:
            Complete IRData instance
        """
        # Extract imports from operations
        imports = self._extract_imports_from_operations(operations_data)

        # Combine all data (with generated_at at top level for templates)
        strawberry_data = {
            "version": 1,
            "generated_at": datetime.now().isoformat(),
            "operations": operations_data["queries"]
            + operations_data["mutations"]
            + operations_data["subscriptions"],
            "domain_types": domain_data["types"],
            "interfaces": domain_data["interfaces"],
            "scalars": domain_data.get("scalars", []),
            "enums": domain_data["enums"],
            "inputs": domain_data.get("inputs", []),
            "input_types": operations_data["input_types"],
            "result_types": operations_data["result_types"],
            "node_specs": node_specs or [],  # Include node_specs for templates
            "types": domain_data["types"],  # Alias for domain_types for backward compatibility
            "config": config,
            "imports": imports,
            "raw_queries": operations_data.get("raw_queries", []),
            "raw_mutations": operations_data.get("raw_mutations", []),
            "raw_subscriptions": operations_data.get("raw_subscriptions", []),
            "queries": operations_data["queries"],
            "mutations": operations_data["mutations"],
            "subscriptions": operations_data["subscriptions"],
            "operations_ir": operations_data,
            "metadata": {
                "ast_file_count": len(source_files) if source_files else 0,
                "interface_count": len(domain_data["interfaces"]),
                "enum_count": len(domain_data["enums"]),
                "scalar_count": len(domain_data.get("scalars", [])),
                "input_count": len(domain_data.get("inputs", [])),
                "node_spec_count": len(node_specs) if node_specs else 0,
                "total_operations": operations_data["metadata"]["total_count"],
                "total_queries": operations_data["metadata"].get("total_queries", 0),
                "total_mutations": operations_data["metadata"].get("total_mutations", 0),
                "total_subscriptions": operations_data["metadata"].get("total_subscriptions", 0),
                "operations_meta": operations_data["metadata"],
            },
        }

        # Create metadata for IRData
        metadata = IRMetadata(
            version=1,
            source_files=len(source_files) if source_files else 0,  # Count of source files
            builder_type="strawberry",
            generated_at=datetime.now().isoformat(),
        )

        # Create IR data with proper structure
        ir_data = IRData(metadata=metadata, data=strawberry_data)
        return ir_data

    def _extract_imports_from_operations(self, operations_data: dict[str, Any]) -> dict[str, list[str]]:
        """Extract import types from operations data.

        Args:
            operations_data: Operations IR data

        Returns:
            Dictionary with 'strawberry' and 'domain' import lists
        """
        strawberry_imports = set()
        domain_imports = set()

        # Collect all operations
        all_operations = (
            operations_data.get("queries", [])
            + operations_data.get("mutations", [])
            + operations_data.get("subscriptions", [])
        )

        # Extract types from operation variables
        for operation in all_operations:
            variables = operation.get("variables", [])
            for variable in variables:
                var_type = variable.get("type", "")

                # Remove GraphQL modifiers (! for required, [] for arrays)
                clean_type = var_type.replace("!", "").replace("[", "").replace("]", "")

                # Categorize the import type
                if clean_type == "Upload":
                    strawberry_imports.add(clean_type)
                elif clean_type.endswith("Input") or clean_type in ["DiagramFormatGraphQL"]:
                    domain_imports.add(clean_type)

        return {"strawberry": sorted(list(strawberry_imports)), "domain": sorted(list(domain_imports))}