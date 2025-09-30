"""Backend IR builder using the step-based pipeline."""

from __future__ import annotations

import logging

from dipeo.config.base_logger import get_module_logger
from typing import Any

from dipeo.domain.codegen.ir_builder_port import IRData, IRMetadata
from dipeo.infrastructure.codegen.ir_builders.core.base import BaseIRBuilder
from dipeo.infrastructure.codegen.ir_builders.core.base_steps import BaseAssemblerStep
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

class BackendAssemblerStep(BaseAssemblerStep):
    """Assemble final backend IR data from pipeline results."""

    def __init__(self):
        super().__init__(name="backend_assembler", required=True)

    def get_dependency_names(self) -> list[str]:
        """Get list of required dependency step names.

        Returns:
            List of step names this assembler depends on
        """
        return [
            "extract_node_specs",
            "extract_enums",
            "extract_domain_models",
            "extract_integrations",
            "extract_conversions",
            "extract_typescript_indexes",
            "build_node_factory",
            "build_category_metadata",
        ]

    def handle_missing_dependency(self, dep_name: str) -> Any:
        """Handle missing dependency data with appropriate defaults.

        Args:
            dep_name: Name of missing dependency

        Returns:
            Default value for missing dependency
        """
        # Return empty list for list-based dependencies
        if dep_name in ["extract_node_specs", "extract_enums", "extract_integrations"]:
            return []
        # Return empty dict for dict-based dependencies
        if dep_name in ["build_node_factory", "build_category_metadata", "extract_conversions", "extract_typescript_indexes"]:
            return {}
        # Domain models needs special structure
        if dep_name == "extract_domain_models":
            return {"models": [], "aliases": {}, "newtypes": []}
        return None

    def assemble_ir(self, dependency_data: dict[str, Any], context: Any) -> dict[str, Any]:
        """Assemble backend IR from dependency data.

        Args:
            dependency_data: Dictionary of data from dependencies
            context: Build context

        Returns:
            Assembled backend IR data dictionary
        """
        # Get results from dependencies
        node_specs = dependency_data.get("extract_node_specs") or []
        enums = dependency_data.get("extract_enums") or []
        domain_models = dependency_data.get("extract_domain_models") or {"models": [], "aliases": {}}
        integrations = dependency_data.get("extract_integrations") or []
        conversions = dependency_data.get("extract_conversions") or {}
        typescript_indexes = dependency_data.get("extract_typescript_indexes") or {}
        node_factory = dependency_data.get("build_node_factory") or {}
        category_metadata = dependency_data.get("build_category_metadata") or {}

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
            "node_specs": node_specs,
            "enums": enums,
            "domain_models": domain_models,
            "types": models,
            "type_aliases": aliases,
            "node_factory": node_factory,
            "integrations": integrations,
            "conversions": conversions,
            "typescript_indexes": typescript_indexes,
            "metadata": {
                "node_count": len(node_specs),
                "enum_count": len(enums),
                "model_count": len(models),
                "alias_count": len(aliases),
                "integration_count": len(integrations),
                "category_metadata": category_metadata,
            },
        }

        return backend_data

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
