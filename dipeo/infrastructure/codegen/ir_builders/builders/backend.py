"""Backend IR builder using the step-based pipeline."""

from __future__ import annotations

import logging

from dipeo.config.base_logger import get_module_logger
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
from dipeo.infrastructure.codegen.ir_builders.modules.typescript_indexes import (
    ExtractTypescriptIndexesStep,
)

logger = get_module_logger(__name__)

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
            "extract_typescript_indexes",
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
            typescript_indexes = context.get_step_data("extract_typescript_indexes")
            node_factory = context.get_step_data("build_node_factory")
            category_metadata = context.get_step_data("build_category_metadata")

            # Assemble backend data matching original structure
            # Handle domain_models structure properly
            if domain_models and isinstance(domain_models, dict):
                models = domain_models.get("models", [])
                # Ensure aliases is always a dict
                aliases = domain_models.get("aliases", {})
                if isinstance(aliases, list):
                    # Convert list to dict if needed (empty case)
                    aliases = (
                        {}
                        if not aliases
                        else {a.get("name", f"alias_{i}"): a for i, a in enumerate(aliases)}
                    )
            else:
                models = []
                aliases = {}
                # Create proper empty domain_models structure
                domain_models = {"models": [], "aliases": {}}

            backend_data = {
                "version": 1,
                "generated_at": context.create_metadata({})["generated_at"],
                "node_specs": node_specs or [],
                "enums": enums or [],
                "domain_models": domain_models,
                "types": models,
                "type_aliases": aliases,
                "node_factory": node_factory or {},
                "integrations": integrations or [],
                "conversions": conversions or {},
                "typescript_indexes": typescript_indexes,
                "metadata": {
                    "node_count": len(node_specs) if node_specs else 0,
                    "enum_count": len(enums) if enums else 0,
                    "model_count": len(models),
                    "alias_count": len(aliases),
                    "integration_count": len(integrations) if integrations else 0,
                    "category_metadata": category_metadata or {},
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
                ExtractTypescriptIndexesStep(),
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
