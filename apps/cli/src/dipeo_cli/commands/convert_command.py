"""Convert command for diagram format conversion."""

import json
from pathlib import Path

import yaml

from .base import DiagramLoader


class ConvertCommand:
    """Command for converting between diagram formats."""

    def __init__(self):
        self.loader = DiagramLoader()

    def execute(
        self,
        input_path: str,
        output_path: str,
        from_format: str | None = None,
        to_format: str | None = None,
    ):
        """Convert between diagram formats using the integrated diagram service."""
        print(f"📝 Converting: {input_path} → {output_path}")

        # Auto-detect formats from file extensions if not provided
        if not from_format:
            from_format = self._detect_format_from_path(input_path, is_input=True)

        if not to_format:
            to_format = self._detect_format_from_path(output_path, is_input=False)

        print(f"  Format: {from_format} → {to_format}")

        # If same format, just copy the file
        if from_format == to_format:
            self._copy_with_formatting(input_path, output_path)
            print("✓ Conversion complete")
            return

        # Use the diagram service for format conversion
        try:
            # Import required modules
            from dipeo.infrastructure.diagram.drivers.diagram_service import DiagramService
            from dipeo.infrastructure.shared.adapters import LocalFileSystemAdapter
            from dipeo.config import get_settings

            # Create diagram service using unified config
            settings = get_settings()
            filesystem = LocalFileSystemAdapter(base_path=Path(settings.storage.base_dir))
            diagram_service = DiagramService(
                filesystem=filesystem,
                base_path=Path(settings.storage.base_dir) / settings.storage.data_dir
            )

            # Load the diagram data
            with Path(input_path).open(encoding="utf-8") as f:
                content = f.read()

            # Convert: deserialize from source format, serialize to target format
            diagram = diagram_service.deserialize(content, from_format)
            output_content = diagram_service.serialize(diagram, to_format)

            # Save the converted content
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with Path(output_path).open("w", encoding="utf-8") as f:
                f.write(output_content)

            print("✓ Conversion complete")

        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            raise

    def _detect_format_from_path(self, path: str, is_input: bool) -> str:
        """Auto-detect format from file extension."""
        file_name = Path(path).name.lower()

        if file_name.endswith(".native.json"):
            return "native"
        if file_name.endswith(".light.yaml"):
            return "light"
        if file_name.endswith(".readable.yaml"):
            return "readable"
        file_type = "input" if is_input else "output"
        raise ValueError(
            f"Cannot determine format from {file_type} file: {path}"
        )

    def _copy_with_formatting(self, input_path: str, output_path: str):
        """Copy file with proper formatting."""
        # Load and save to handle any formatting differences
        data = self.loader.load_diagram(input_path)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with Path(output_path).open("w", encoding="utf-8") as f:
            if output_path.endswith(".json"):
                json.dump(data, f, indent=2)
            else:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
