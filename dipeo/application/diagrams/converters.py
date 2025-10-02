"""Diagram format conversion utilities."""

import json
from pathlib import Path
from typing import Optional

import yaml

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.enums import DiagramFormat

logger = get_module_logger(__name__)


class DiagramConverter:
    """Converts diagrams between different formats."""

    def convert(
        self,
        input_path: str,
        output_path: str,
        from_format: DiagramFormat,
        to_format: DiagramFormat,
    ) -> bool:
        """Convert a diagram from one format to another."""
        try:
            # Load the input diagram
            with open(input_path, "r", encoding="utf-8") as f:
                if from_format == DiagramFormat.NATIVE:
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)

            # Convert format if needed
            if from_format != to_format:
                data = self._transform_format(data, from_format, to_format)

            # Save in the target format
            with open(output_path, "w", encoding="utf-8") as f:
                if to_format == DiagramFormat.NATIVE:
                    json.dump(data, f, indent=2)
                else:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Converted {input_path} from {from_format} to {to_format}")
            return True

        except Exception as e:
            logger.error(f"Failed to convert diagram: {e}")
            return False

    def _transform_format(self, data: dict, from_format: DiagramFormat, to_format: DiagramFormat) -> dict:
        """Transform diagram data between formats."""
        # For now, formats are compatible - just pass through
        # In the future, this could handle structural transformations
        return data