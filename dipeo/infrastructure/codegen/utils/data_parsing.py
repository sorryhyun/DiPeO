"""Core utilities for codegen system - DiPeO output parsing."""

import ast
import json


def parse_dipeo_output(data):
    """Parse DiPeO output (JSON or Python dict string)."""
    if not isinstance(data, str):
        return data
    try:
        return ast.literal_eval(data)
    except (ValueError, SyntaxError):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}
