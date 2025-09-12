"""
Extract branded types from TypeScript AST for GraphQL scalar generation.
"""

import os
from pathlib import Path
from typing import Any

from projects.codegen.code.core.utils import parse_dipeo_output


def extract_branded_types_from_ast(ast_data: dict[str, Any]) -> list[dict[str, str]]:
    """Extract branded type definitions from TypeScript AST data."""
    branded_types = []

    # Get types from the AST
    types = ast_data.get("types", [])

    for type_def in types:
        name = type_def.get("name", "")
        type_str = type_def.get("type", "")

        # Check if it's a branded type (contains __brand)
        if "__brand" in type_str and type_def.get("isExported", False):
            # Extract the brand value (e.g., 'NodeID' from the brand)
            branded_types.append(
                {
                    "name": name,
                    "scalar_name": f"{name}Scalar",
                    "description": f'Unique identifier type for {name.replace("ID", "").lower()} entities',
                }
            )

    return branded_types


def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Main entry point for GraphQL scalar extraction.

    Reads TypeScript AST files and extracts all branded types for scalar generation.
    """

    all_scalars = []

    # Debug: Log what we receive
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(f"Received inputs keys: {list(inputs.keys())}")

    # Try multiple input formats that DB node might use
    ast_files = []

    # Check for 'default' key (most common)
    if "default" in inputs:
        data = inputs["default"]

        # Handle string input that needs evaluation
        if isinstance(data, str):
            data = parse_dipeo_output(data)
            if not data:
                logger.debug(f"Could not parse string input: {data[:100]}")
                data = None

        if isinstance(data, dict):
            # Single file result
            ast_files = [data]
        elif isinstance(data, list):
            # Multiple file results
            ast_files = data
        elif data:
            logger.debug(f"Unexpected 'default' type: {type(data)}")

    # Check for direct list (some DB nodes return this way)
    elif isinstance(inputs, list):
        ast_files = inputs

    # Check if inputs itself is the AST data
    elif "types" in inputs and isinstance(inputs.get("types"), list):
        ast_files = [inputs]

    # Process any AST files we found
    for item in ast_files:
        # Handle string items
        if isinstance(item, str):
            item = parse_dipeo_output(item)
            if not item:
                continue

        if isinstance(item, dict):
            # Check if it's AST data (has 'types' key)
            if "types" in item:
                scalars = extract_branded_types_from_ast(item)
                all_scalars.extend(scalars)
            # Check if it's a wrapper with content
            elif "content" in item and isinstance(item["content"], dict):
                scalars = extract_branded_types_from_ast(item["content"])
                all_scalars.extend(scalars)

    # If still no scalars, try filesystem fallback
    if not all_scalars:
        logger.debug("No scalars from inputs, trying filesystem fallback")
        base_dir = Path(os.getenv("DIPEO_BASE_DIR", os.getcwd()))
        temp_dir = base_dir / "temp"

        core_files = [
            "core/diagram.ts.json",
            "core/execution.ts.json",
        ]

        for file_path in core_files:
            ast_file = temp_dir / file_path
            if ast_file.exists():
                with open(ast_file) as f:
                    content = f.read()
                    ast_data = parse_dipeo_output(content)
                    scalars = extract_branded_types_from_ast(ast_data)
                    all_scalars.extend(scalars)

    # Remove duplicates (if any)
    seen = set()
    unique_scalars = []
    for scalar in all_scalars:
        if scalar["name"] not in seen:
            seen.add(scalar["name"])
            unique_scalars.append(scalar)

    # Sort by name for consistent output
    unique_scalars.sort(key=lambda x: x["name"])

    # Add metadata
    from datetime import datetime

    result = {
        "scalars": unique_scalars,
        "generated_at": datetime.now().isoformat(),
        "total_count": len(unique_scalars),
    }

    return result


if __name__ == "__main__":
    # Test with mock data
    test_ast = {
        "types": [
            {
                "name": "NodeID",
                "type": "string & { readonly __brand: 'NodeID' }",
                "isExported": True,
            },
            {
                "name": "ArrowID",
                "type": "string & { readonly __brand: 'ArrowID' }",
                "isExported": True,
            },
        ]
    }

    result = extract_branded_types_from_ast(test_ast)
    import json
    print(json.dumps(result, indent=2))
