"""TypeScript index extraction module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dipeo.infrastructure.codegen.ir_builders.core import (
    BuildContext,
    BuildStep,
    StepResult,
    StepType,
)
from dipeo.infrastructure.codegen.ir_builders.utils import camel_to_snake


class ExtractTypescriptIndexesStep(BuildStep):
    """Step to extract TypeScript index configurations."""

    def __init__(self):
        """Initialize TypeScript indexes extraction step."""
        super().__init__(
            name="extract_typescript_indexes",
            step_type=StepType.EXTRACT,
            required=True
        )

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Extract TypeScript index configuration.

        Args:
            context: Build context with utilities
            input_data: Base directory path or AST data (not used directly)

        Returns:
            StepResult with TypeScript index configuration
        """
        base_dir = context.base_dir

        indexes = self._extract_typescript_indexes(base_dir)

        return StepResult(
            success=True,
            data=indexes,
            metadata={
                "node_specs_count": len(indexes["node_specs"]),
                "types_count": len(indexes["types"]),
                "utils_count": len(indexes["utils"]),
            }
        )

    def _extract_typescript_indexes(self, base_dir: Path) -> dict[str, Any]:
        """Generate TypeScript index exports configuration.

        Args:
            base_dir: Base directory path for the project

        Returns:
            Dictionary containing TypeScript index configuration
        """
        indexes = {
            "node_specs": [],
            "types": [],
            "utils": [],
        }

        # Scan for TypeScript files that should be indexed
        specs_dir = base_dir / "dipeo/models/src/node-specs"
        if specs_dir.exists():
            for spec_file in specs_dir.glob("*.spec.ts"):
                spec_name = spec_file.stem.replace(".spec", "")
                registry_key = camel_to_snake(spec_name)
                indexes["node_specs"].append(
                    {
                        "file": spec_file.name,
                        "name": spec_name,
                        "registry_key": registry_key,
                    }
                )

        return indexes