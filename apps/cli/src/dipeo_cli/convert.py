"""
Convert command implementation for DiPeO CLI.
"""

import json
from pathlib import Path

from .api_client import DiPeoAPIClient
from .utils import DiagramLoader


async def convert_command(args: list[str]) -> None:
    """Execute convert command - converts between JSON and YAML formats using backend API"""
    if len(args) < 2:
        print("Error: Usage: convert <input> <output>")
        return

    input_path = args[0]
    output_path = args[1]

    try:
        # Load diagram locally (still need to read the file)
        diagram = DiagramLoader.load(input_path)

        # Determine output format from file extension
        output_ext = Path(output_path).suffix.lower()
        if output_ext in [".yaml", ".yml"]:
            format_name = "native_yaml"
        elif output_ext == ".json":
            format_name = "native"
        else:
            # Try to detect from filename patterns
            if "light" in output_path.lower():
                format_name = "light"
            elif "readable" in output_path.lower():
                format_name = "readable"
            else:
                format_name = "native"  # Default to native JSON

        # Use backend API for conversion
        async with DiPeoAPIClient() as client:
            # Debug: print what we're sending
            if "--debug" in args:
                print(f"Sending diagram data: {json.dumps(diagram, indent=2)[:200]}...")
                print(f"Format: {format_name}")

            result = await client.convert_diagram(
                diagram_data=diagram,
                format=format_name,
                include_metadata=True
            )

            if result["content"]:
                # Write the converted content
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w") as f:
                    f.write(result["content"])

                print(f"✓ Converted: {input_path} → {output_path} (format: {result['format']})")
            else:
                print("Error: Conversion returned empty content")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error during conversion: {e}")
