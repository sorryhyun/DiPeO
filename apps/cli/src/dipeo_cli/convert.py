"""
Convert command implementation for DiPeO CLI.
"""

from typing import List

from .utils import DiagramLoader


def convert_command(args: List[str]) -> None:
    """Execute convert command - converts between JSON and YAML formats"""
    if len(args) < 2:
        print("Error: Usage: convert <input> <output>")
        return

    input_path = args[0]
    output_path = args[1]

    try:
        # Load diagram
        diagram = DiagramLoader.load(input_path)

        # Save in new format
        DiagramLoader.save(diagram, output_path)

        print(f"✓ Converted: {input_path} → {output_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error during conversion: {e}")
