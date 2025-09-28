"""Backend IR builder using the step-based pipeline."""

from __future__ import annotations

import logging
from typing import Any

from dipeo.domain.codegen.ir_builder_port import IRData, IRMetadata
from dipeo.infrastructure.codegen.ir_builders.core.base import BaseIRBuilder
from dipeo.infrastructure.codegen.ir_builders.core.steps import BuildStep, StepResult, StepType
from dipeo.infrastructure.codegen.ir_builders.modules.domain_models import (
    ExtractConversionsStep,
    ExtractDomainModelsStep,
    ExtractEnumsStep,
    ExtractIntegrationsStep,
)
from dipeo.infrastructure.codegen.ir_builders.modules.node_specs import (
    BuildCategoryMetadataStep,
    BuildNodeFactoryStep,
    ExtractNodeSpecsStep,
)

logger = logging.getLogger(__name__)


class BackendAssemblerStep(BuildStep):
    """Assemble final backend IR data from pipeline results."""

    def __init__(self):
        super().__init__(
            name="backend_assembler",
            step_type=StepType.ASSEMBLE,
        )
        # Set dependencies after initialization
        self._dependencies = [
            "extract_node_specs",
            "extract_enums",
            "extract_domain_models",
            "extract_integrations",
            "extract_conversions",
            "build_node_factory",
            "build_category_metadata",
        ]

    def execute(self, context: Any, data: Any) -> StepResult:
        """Assemble backend IR from previous step results.

        Args:
            context: Build context
            data: Results from previous steps

        Returns:
            StepResult with assembled backend IR
        """
        try:
            # Get results from previous steps
            node_specs = context.get_step_data("extract_node_specs")
            enums = context.get_step_data("extract_enums")
            domain_models = context.get_step_data("extract_domain_models")
            integrations = context.get_step_data("extract_integrations")
            conversions = context.get_step_data("extract_conversions")
            node_factory = context.get_step_data("build_node_factory")
            category_metadata = context.get_step_data("build_category_metadata")

            # Extract TypeScript indexes
            import os
            from pathlib import Path

            from dipeo.infrastructure.codegen.ir_builders.backend_extractors import (
                extract_typescript_indexes,
            )

            base_dir = Path(os.environ.get("DIPEO_BASE_DIR", "."))
            typescript_indexes = extract_typescript_indexes(base_dir)

            # Assemble backend data matching original structure
            backend_data = {
                "version": 1,
                "generated_at": context.create_metadata({})["generated_at"],
                "node_specs": node_specs,
                "enums": enums,
                "domain_models": domain_models,
                "types": domain_models["models"] if domain_models else [],
                "type_aliases": domain_models["aliases"] if domain_models else {},
                "node_factory": node_factory,
                "integrations": integrations,
                "conversions": conversions or {},
                "typescript_indexes": typescript_indexes,
                "metadata": {
                    "node_count": len(node_specs) if node_specs else 0,
                    "enum_count": len(enums) if enums else 0,
                    "model_count": len(domain_models["models"]) if domain_models else 0,
                    "alias_count": len(domain_models["aliases"]) if domain_models else 0,
                    "integration_count": len(integrations) if integrations else 0,
                    "category_metadata": category_metadata,
                },
            }

            return StepResult(
                success=True,
                data=backend_data,
                metadata={"message": "Successfully assembled backend IR data"},
            )
        except Exception as e:
            logger.error(f"Failed to assemble backend IR: {e}")
            return StepResult(
                success=False,
                error=str(e),
                metadata={"message": f"Backend assembly failed: {e}"},
            )


class BackendBuilder(BaseIRBuilder):
    """Backend IR builder using step-based pipeline.

    Orchestrates:
    - Node specs extraction and factory building
    - Domain models and enum extraction
    - Integrations and conversions extraction
    - Backend-specific assembly and validation
    """

    def _configure_pipeline(self) -> None:
        """Configure the backend pipeline with required steps."""
        # Add extraction steps
        self.orchestrator.add_steps(
            [
                ExtractNodeSpecsStep(),
                ExtractEnumsStep(),
                ExtractDomainModelsStep(),
                ExtractIntegrationsStep(),
                ExtractConversionsStep(),
            ]
        )

        # Add build/transform steps
        self.orchestrator.add_steps(
            [
                BuildNodeFactoryStep(),
                BuildCategoryMetadataStep(),
            ]
        )

        # Add assembly step
        self.orchestrator.add_step(BackendAssemblerStep())

    def get_builder_type(self) -> str:
        """Get builder type identifier.

        Returns:
            'backend'
        """
        return "backend"

    def _assemble_ir_data(self, results: dict[str, StepResult]) -> IRData:
        """Override to use backend assembler results.

        Args:
            results: Pipeline execution results

        Returns:
            Assembled IRData
        """
        # Get backend assembler output
        assembler_result = results.get("backend_assembler")
        if assembler_result and assembler_result.success:
            backend_data = assembler_result.data

            metadata = IRMetadata(
                version=backend_data["version"],
                generated_at=backend_data["generated_at"],
                source_files=len(backend_data.get("typescript_indexes", {})),
                builder_type=self.get_builder_type(),
            )

            return IRData(
                metadata=metadata,
                data=backend_data,
            )

        # Fallback to base implementation if assembler failed
        return super()._assemble_ir_data(results)
