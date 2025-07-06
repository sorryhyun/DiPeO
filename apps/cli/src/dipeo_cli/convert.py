"""
Convert command implementation for DiPeO CLI.
"""

import json
from pathlib import Path

from dipeo.diagram import UnifiedDiagramConverter

from .api_client import DiPeoAPIClient
from .utils import DiagramLoader


async def convert_command(args: list[str]) -> None:
    """Execute convert command - converts between JSON and YAML formats."""
    if len(args) < 2:
        print("Error: Usage: convert <input> <output> [--local]")
        return

    input_path = args[0]
    output_path = args[1]
    use_local = "--local" in args

    try:
        output_ext = Path(output_path).suffix.lower()
        output_name = Path(output_path).stem.lower()

        if "light" in output_name:
            format_name = "light"
        elif "readable" in output_name:
            format_name = "readable"
        elif output_ext in [".yaml", ".yml"]:
            format_name = "light"
        elif output_ext == ".json":
            format_name = "native"
        else:
            format_name = "native"

        if use_local:
            converter = UnifiedDiagramConverter()

            with open(input_path) as f:
                content = f.read()

            domain_diagram = converter.deserialize(content)
            output_content = converter.serialize(domain_diagram, format_name)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(output_content)

            print(
                f"✓ Converted locally: {input_path} → {output_path} (format: {format_name})"
            )
        else:
            diagram = DiagramLoader.load(input_path)

            async with DiPeoAPIClient() as client:
                if "--debug" in args:
                    print(
                        f"Sending diagram data: {json.dumps(diagram, indent=2)[:200]}..."
                    )
                    print(f"Format: {format_name}")

                result = await client.convert_diagram(
                    diagram_data=diagram, format=format_name, include_metadata=True
                )

                if result and result.get("content"):
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w") as f:
                        f.write(result["content"])

                    print(
                        f"✓ Converted: {input_path} → {output_path} (format: {result.get('format', format_name)})"
                    )
                else:
                    print("Error: Conversion returned empty content")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error during conversion: {e}")
