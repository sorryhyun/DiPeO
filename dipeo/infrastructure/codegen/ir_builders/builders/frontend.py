"""Frontend IR builder using the step-based pipeline."""

from __future__ import annotations

import logging

from dipeo.config.base_logger import get_module_logger
from typing import Any

from dipeo.domain.codegen.ir_builder_port import IRData, IRMetadata
from dipeo.infrastructure.codegen.ir_builders.core.base import BaseIRBuilder
from dipeo.infrastructure.codegen.ir_builders.core.context import BuildContext
from dipeo.infrastructure.codegen.ir_builders.core.steps import BuildStep, StepResult, StepType
from dipeo.infrastructure.codegen.ir_builders.core.base_steps import BaseAssemblerStep
from dipeo.infrastructure.codegen.ir_builders.modules.graphql_operations import (
    ExtractGraphQLOperationsStep,
    BuildOperationStringsStep,
    GroupOperationsByEntityStep,
)
from dipeo.infrastructure.codegen.ir_builders.modules.node_specs import ExtractNodeSpecsStep
from dipeo.infrastructure.codegen.ir_builders.modules.ui_configs import (
    BuildNodeRegistryStep,
    ExtractNodeConfigsStep,
    GenerateFieldConfigsStep,
    GenerateTypeScriptModelsStep,
)

logger = get_module_logger(__name__)

class FrontendAssemblerStep(BaseAssemblerStep):
    """Assemble final frontend IR data from pipeline results.

    Migrated to use BaseAssemblerStep template method pattern for reduced code duplication.
    """

    def __init__(self):
        """Initialize frontend assembler step."""
        super().__init__(name="frontend_assembler", required=True)

    def get_dependency_names(self) -> list[str]:
        """Get required dependency step names.

        Returns:
            List of dependency names
        """
        return [
            "extract_node_specs",
            "extract_node_configs",
            "build_node_registry",
            "generate_field_configs",
            "generate_typescript_models",
            "extract_graphql_operations",
            "group_operations_by_entity",
        ]

    def handle_missing_dependency(self, dep_name: str) -> Any:
        """Handle missing dependency data with appropriate defaults.

        Args:
            dep_name: Name of missing dependency

        Returns:
            Default value for the dependency
        """
        # Most dependencies can default to empty collections
        logger.warning(f"Dependency '{dep_name}' missing in {self.name}, using empty default")
        if dep_name in ["extract_node_specs", "extract_graphql_operations"]:
            return []
        else:
            return {}

    def assemble_ir(
        self, dependency_data: dict[str, Any], context: BuildContext
    ) -> dict[str, Any]:
        """Assemble frontend IR from dependency data.

        Args:
            dependency_data: Dictionary with all dependency data
            context: Build context

        Returns:
            Assembled frontend IR dictionary
        """
        # Extract dependency data
        node_specs = dependency_data.get("extract_node_specs")
        node_configs = dependency_data.get("extract_node_configs")
        node_registry = dependency_data.get("build_node_registry")
        field_configs = dependency_data.get("generate_field_configs")
        typescript_models = dependency_data.get("generate_typescript_models")
        operations = dependency_data.get("extract_graphql_operations")
        grouped_operations = dependency_data.get("group_operations_by_entity")

        # Get enums (if extracted by other steps)
        enums = []
        # Note: We would need the original AST data to extract enums
        # For now, we'll leave it empty or get from context if available

        # Separate operations into queries, mutations, subscriptions for backward compatibility
        queries, mutations, subscriptions = self._separate_operations_by_type(operations or [])

        # Assemble frontend data matching original structure
        frontend_data = {
            "version": 1,
            "generated_at": context.create_metadata({})["generated_at"],
            "node_specs": node_specs or [],
            "node_configs": node_configs or {},
            "node_registry": node_registry or {},
            # Also keep registry_data for backward compatibility
            "registry_data": node_registry or {},
            "field_configs": field_configs or {},
            "typescript_models": typescript_models or {},
            "graphql_queries": operations or [],
            # Add separate lists for backward compatibility
            "queries": queries,
            "mutations": mutations,
            "subscriptions": subscriptions,
            "grouped_queries": grouped_operations or {},
            "enums": enums,
            "metadata": {
                "node_count": len(node_specs) if node_specs else 0,
                "config_count": len(node_configs) if node_configs else 0,
                "field_config_count": len(field_configs) if field_configs else 0,
                "model_count": len(typescript_models) if typescript_models else 0,
                "query_count": len(operations) if operations else 0,
                "enum_count": len(enums),
            },
        }

        return frontend_data

    def _separate_operations_by_type(
        self, operations: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Separate operations by type for backward compatibility.

        Args:
            operations: List of all operations

        Returns:
            Tuple of (queries, mutations, subscriptions) lists
        """
        queries = []
        mutations = []
        subscriptions = []

        for op in operations:
            if isinstance(op, dict):
                op_type = op.get("type", "").lower()
                if op_type == "query":
                    queries.append(op)
                elif op_type == "mutation":
                    mutations.append(op)
                elif op_type == "subscription":
                    subscriptions.append(op)

        return queries, mutations, subscriptions

class ExtractFrontendEnumsStep(BuildStep):
    """Extract enums specifically for frontend use."""

    def __init__(self):
        super().__init__(
            name="extract_frontend_enums",
            step_type=StepType.EXTRACT,
        )

    def execute(self, context: BuildContext, data: dict[str, Any]) -> StepResult:
        """Extract enums from AST.

        Args:
            context: Build context
            data: AST file dictionary

        Returns:
            StepResult with enums
        """
        try:
            from dipeo.infrastructure.codegen.ir_builders.utils import extract_enums_from_ast

            enums = extract_enums_from_ast(data)

            return StepResult(
                success=True,
                data=enums,
                metadata={"message": f"Successfully extracted {len(enums)} enums"},
            )
        except Exception as e:
            logger.error(f"Failed to extract frontend enums: {e}")
            return StepResult(
                success=False,
                error=str(e),
                metadata={"message": f"Enum extraction failed: {e}"},
            )

class WriteSnapshotStep(BuildStep):
    """Write frontend IR snapshot to disk for debugging."""

    def __init__(self, output_path: str = "projects/codegen/ir/frontend_ir.json"):
        super().__init__(
            name="write_snapshot",
            step_type=StepType.VALIDATE,  # Using validate as it's a post-processing step
        )
        self._dependencies = ["frontend_assembler"]
        self.output_path = output_path

    def execute(self, context: BuildContext, data: Any) -> StepResult:
        """Write IR snapshot to disk.

        Args:
            context: Build context
            data: Input data (unused, uses context)

        Returns:
            StepResult with write status
        """
        try:
            import json
            from pathlib import Path

            # Get assembled data
            frontend_data = context.get_step_data("frontend_assembler")
            if not frontend_data:
                return StepResult(
                    success=False,
                    error="No frontend data to write",
                )

            # Ensure output directory exists
            output_file = Path(self.output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write snapshot
            with open(output_file, "w") as f:
                json.dump(frontend_data, f, indent=2)

            return StepResult(
                success=True,
                data={"snapshot_path": str(output_file)},
                metadata={"message": f"Wrote frontend IR snapshot to {output_file}"},
            )
        except Exception as e:
            logger.error(f"Failed to write frontend snapshot: {e}")
            return StepResult(
                success=False,
                error=str(e),
                metadata={"message": f"Snapshot write failed: {e}"},
            )

class FrontendBuilder(BaseIRBuilder):
    """Frontend IR builder using step-based pipeline.

    Orchestrates:
    - Node specs and UI configuration extraction
    - Field configuration generation
    - TypeScript model generation
    - GraphQL query extraction and grouping
    - Frontend-specific assembly
    """

    def __init__(self, config_path: str | None = None):
        """Initialize frontend builder.

        Args:
            config_path: Optional configuration path
        """
        self.write_snapshot = True  # Can be configured
        super().__init__(config_path)

    def _configure_pipeline(self) -> None:
        """Configure the frontend pipeline with required steps."""
        # Add extraction steps
        self.orchestrator.add_steps(
            [
                ExtractNodeSpecsStep(),
                ExtractNodeConfigsStep(),
                ExtractFrontendEnumsStep(),
                ExtractGraphQLOperationsStep(),
            ]
        )

        # Add generation/build steps
        self.orchestrator.add_steps(
            [
                BuildNodeRegistryStep(),
                GenerateFieldConfigsStep(),
                GenerateTypeScriptModelsStep(),
                BuildOperationStringsStep(),  # Applies camelCase conversion to field names
                GroupOperationsByEntityStep(),
            ]
        )

        # Add assembly step
        self.orchestrator.add_step(FrontendAssemblerStep())

        # Add optional snapshot writer
        if self.write_snapshot:
            self.orchestrator.add_step(WriteSnapshotStep())

    def get_builder_type(self) -> str:
        """Get builder type identifier.

        Returns:
            'frontend'
        """
        return "frontend"

    def _assemble_ir_data(self, results: dict[str, StepResult]) -> IRData:
        """Override to use frontend assembler results.

        Args:
            results: Pipeline execution results

        Returns:
            Assembled IRData
        """
        # Get frontend assembler output
        assembler_result = results.get("frontend_assembler")
        if assembler_result and assembler_result.success:
            frontend_data = assembler_result.data

            metadata = IRMetadata(
                version=frontend_data["version"],
                generated_at=frontend_data["generated_at"],
                source_files=frontend_data["metadata"]["node_count"],
                builder_type=self.get_builder_type(),
            )

            return IRData(
                metadata=metadata,
                data=frontend_data,
            )

        # Fallback to base implementation
        return super()._assemble_ir_data(results)
