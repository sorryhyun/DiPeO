#!/usr/bin/env python3
"""Example Python file for Code Job node execution."""

import json
from typing import Any


def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Main function that processes inputs from connected nodes.

    Args:
        inputs: Dictionary with connection labels as keys

    Returns:
        Dictionary with results
    """
    # Access inputs by connection labels
    data_source = inputs.get("data_source", "No data source provided")
    config = inputs.get("config", {})

    # Process the data
    result = {
        "message": f"Processed data from: {data_source}",
        "config_keys": list(config.keys()) if isinstance(config, dict) else [],
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "input_count": len(inputs),
    }

    # Example: If we have numeric data, calculate something
    if "numbers" in inputs and isinstance(inputs["numbers"], list):
        result["sum"] = sum(inputs["numbers"])
        result["average"] = sum(inputs["numbers"]) / len(inputs["numbers"])

    return result


def process_text(inputs: dict[str, Any]) -> str:
    """Alternative function that can be called by setting functionName."""
    text = inputs.get("text", "")
    return text.upper() if isinstance(text, str) else str(text)


if __name__ == "__main__":
    # For testing standalone
    test_inputs = {
        "data_source": "test_source",
        "config": {"key1": "value1", "key2": "value2"},
        "numbers": [1, 2, 3, 4, 5],
    }
    print(json.dumps(main(test_inputs), indent=2))
