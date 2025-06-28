"""
Convert command implementation for DiPeO CLI.
"""

import json
from pathlib import Path

from dipeo_diagram import UnifiedDiagramConverter, backend_to_graphql
from .api_client import DiPeoAPIClient
from .utils import DiagramLoader


async def convert_command(args: list[str]) -> None:
    """Execute convert command - converts between JSON and YAML formats"""
    if len(args) < 2:
        print("Error: Usage: convert <input> <output> [--local]")
        return

    input_path = args[0]
    output_path = args[1]
    use_local = "--local" in args

    try:
        # Determine output format from file extension and filename
        output_ext = Path(output_path).suffix.lower()
        output_name = Path(output_path).stem.lower()
        
        # Check filename patterns first
        if "light" in output_name:
            format_name = "light"
        elif "readable" in output_name:
            format_name = "readable"
        elif output_ext in [".yaml", ".yml"]:
            # Default YAML format is light
            format_name = "light"
        elif output_ext == ".json":
            format_name = "native"
        else:
            format_name = "native"  # Default to native JSON

        if use_local:
            # Use local conversion via dipeo_diagram
            converter = UnifiedDiagramConverter()
            
            # Read the file content
            with open(input_path, 'r') as f:
                content = f.read()
            
            # Deserialize from input format
            domain_diagram = converter.deserialize(content)
            
            # Serialize to output format
            output_content = converter.serialize(domain_diagram, format_name)
            
            # Write the converted content
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(output_content)

            print(
                f"✓ Converted locally: {input_path} → {output_path} (format: {format_name})"
            )
        else:
            # Load diagram locally (still need to read the file)
            diagram = DiagramLoader.load(input_path)
            
            # Use backend API for conversion
            async with DiPeoAPIClient() as client:
                # Debug: print what we're sending
                if "--debug" in args:
                    print(f"Sending diagram data: {json.dumps(diagram, indent=2)[:200]}...")
                    print(f"Format: {format_name}")

                result = await client.convert_diagram(
                    diagram_data=diagram, format=format_name, include_metadata=True
                )

                if result["content"]:
                    # Write the converted content
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w") as f:
                        f.write(result["content"])

                    print(
                        f"✓ Converted: {input_path} → {output_path} (format: {result['format']})"
                    )
                else:
                    print("Error: Conversion returned empty content")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error during conversion: {e}")
