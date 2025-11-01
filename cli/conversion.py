"""Diagram format conversion and export functionality."""

from pathlib import Path

from dipeo.application.bootstrap import Container
from dipeo.config.base_logger import get_module_logger

from .diagram_loader import DiagramLoader

logger = get_module_logger(__name__)


class DiagramConverter:
    """Handles diagram format conversion and export."""

    def __init__(self, container: Container):
        self.container = container
        self.diagram_loader = DiagramLoader()

    async def convert_diagram(
        self,
        input_path: str,
        output_path: str,
        from_format: str | None = None,
        to_format: str | None = None,
    ) -> bool:
        """Convert between diagram formats."""
        try:
            from dipeo.application.diagram.use_cases.serialize_diagram import (
                SerializeDiagramUseCase,
            )

            input_file = Path(input_path)
            if not input_file.exists():
                print(f"❌ Input file not found: {input_path}")
                return False

            if not from_format:
                from_format = self.diagram_loader.detect_format(input_path)
            if not to_format:
                to_format = self.diagram_loader.detect_format(output_path)

            with open(input_path, encoding="utf-8") as f:
                content = f.read()

            await self.diagram_loader.initialize()
            use_case = SerializeDiagramUseCase(self.diagram_loader.serializer)

            converted_content = use_case.convert_format(content, to_format, from_format)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(converted_content)

            print(f"✅ Converted {input_path} to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Diagram conversion failed: {e}")
            return False

    async def export_diagram(
        self,
        diagram_path: str,
        output_path: str,
        format_type: str | None = None,
    ) -> bool:
        """Export diagram to Python script."""
        try:
            from dipeo.domain.diagram.compilation import PythonDiagramCompiler

            (
                domain_diagram,
                diagram_data,
                diagram_file_path,
            ) = await self.diagram_loader.load_and_deserialize(diagram_path, format_type)

            if not domain_diagram:
                print(f"❌ Failed to load diagram: {diagram_path}")
                return False

            compiler = PythonDiagramCompiler()
            return compiler.export(domain_diagram, output_path)

        except Exception as e:
            logger.error(f"Diagram export failed: {e}")
            import traceback

            traceback.print_exc()
            return False
