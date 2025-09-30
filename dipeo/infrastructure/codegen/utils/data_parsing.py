"""Core utilities for codegen system - DiPeO output parsing."""
import ast
import json


def parse_dipeo_output(data):
    """Parse DiPeO output that could be JSON or Python dict string.

    Args:
        data: The data to parse - could be a string (JSON or Python dict format) or already parsed data

    Returns:
        Parsed data as a Python object, or empty dict if parsing fails
    """
    if not isinstance(data, str):
        return data
    try:
        return ast.literal_eval(data)
    except (ValueError, SyntaxError):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}