"""Common utility functions for node handlers."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from ..types import ExecutionContext
from src.common.processors import OutputProcessor
from .. import executor_utils

logger = logging.getLogger(__name__)

# Regex pattern for {{var}} placeholders
_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")


def safe_eval(expr: str, inputs: Dict[str, Any], ctx: ExecutionContext) -> bool:
    """Tiny, dependency‑free expression evaluator.

    Supported:
      * Python boolean/arithmetic operators
      * JS aliases: &&, ||, ===, !==
      * Variable placeholders: {{var}} or bare identifiers
      * Special "executionCount" variable (loop counter)
    """

    namespace: Dict[str, Any] = {"executionCount": ctx.exec_cnt, **inputs}

    # Flatten previous node outputs for easy access
    for node_id, output in ctx.outputs.items():
        if isinstance(output, dict):
            namespace.update(output)
        else:
            namespace[node_id] = output

    # Replace {{var}} placeholders early
    def _tpl(match: re.Match[str]) -> str:
        val = namespace.get(match.group(1))
        return _fmt(val)

    expr = _VAR_PATTERN.sub(_tpl, expr)

    # Replace bare identifiers with their literal value
    for key, val in namespace.items():
        expr = re.sub(rf"\b{re.escape(key)}\b", _fmt(val), expr)

    # Normalise JS‑style logical operators to Python
    expr = (
        expr.replace("&&", " and ")
        .replace("||", " or ")
        .replace("===", "==")
        .replace("!==", "!=")
    )

    try:
        return bool(eval(expr, {"__builtins__": {}}, {}))  # nosec B307 – controlled input
    except Exception:
        logger.debug("Evaluation error for expression %s", expr, exc_info=True)
        return False


def _fmt(val: Any) -> str:
    """Return a Python literal representation suitable for eval."""
    if val is None:
        return "None"
    if isinstance(val, str):
        return f'"{val}"'
    return str(val)


def process_inputs(inputs: Dict[str, Any]) -> List[Any]:
    """Process inputs to extract values and handle special output types.
    
    This is the canonical version that properly handles PersonJob outputs
    using the OutputProcessor to unwrap structured outputs.
    
    Args:
        inputs: Dictionary of inputs from connected nodes
        
    Returns:
        List of processed input values
    """
    if not inputs:
        return []
    
    processed = []
    for value in inputs.values():
        # Use OutputProcessor to properly unwrap structured outputs
        unwrapped = OutputProcessor.unwrap(value)
        processed.append(unwrapped)
    
    return processed


def substitute_variables(template: str, mapping: Dict[str, Any]) -> str:
    """Replace {{key}}, ${key}, $key placeholders with values from mapping.
    
    This is a thin wrapper around executor_utils.substitute_variables that also
    supports $var syntax (without braces).
    
    Args:
        template: String containing variable placeholders
        mapping: Dictionary mapping variable names to values
        
    Returns:
        String with all placeholders replaced
    """
    # First use the standard executor_utils function for {{key}} syntax
    result = executor_utils.substitute_variables(template, mapping)
    
    # Then handle ${key} and $key syntax
    for k, v in mapping.items():
        result = (
            result.replace(f"${{{k}}}", str(v))
                  .replace(f"${k}", str(v))
        )
    
    return result


def get_api_key(api_key_id: str, context: ExecutionContext) -> Optional[str]:
    """Get API key from execution context.
    
    Args:
        api_key_id: ID of the API key to retrieve
        context: Execution context containing API keys
        
    Returns:
        The API key value if found, None otherwise
    """
    if not hasattr(context, 'api_keys'):
        return None
    
    api_key_info = context.api_keys.get(api_key_id)
    if isinstance(api_key_info, dict):
        return api_key_info.get('key')
    return api_key_info if isinstance(api_key_info, str) else None


def log_action(logger: logging.Logger, node_id: str, action: str, **extra) -> None:
    """Consistent logging helper for node actions.
    
    Args:
        logger: Logger instance to use
        node_id: ID of the node performing the action
        action: Description of the action being performed
        **extra: Additional context to include in the log
    """
    log_data = {
        "node_id": node_id,
        "action": action,
        **extra
    }
    logger.info(f"[{node_id}] {action}", extra=log_data)