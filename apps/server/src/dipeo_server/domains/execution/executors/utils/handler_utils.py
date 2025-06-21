"""Common utility functions for node handlers."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from dipeo_domain import ExecutionContext
from dipeo_server.core.processors import OutputProcessor
from .. import executor_utils

logger = logging.getLogger(__name__)

# Regex pattern for {{var}} placeholders
_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")


def safe_eval(expr: str, inputs: Dict[str, Any], ctx: ExecutionContext) -> bool:
    # Tiny, dependency‑free expression evaluator.

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
    # Process inputs to extract values and handle special output types.
    if not inputs:
        return []
    
    processed = []
    for value in inputs.values():
        # Use OutputProcessor to properly unwrap structured outputs
        unwrapped = OutputProcessor.unwrap(value)
        processed.append(unwrapped)
    
    return processed


def substitute_variables(template: str, mapping: Dict[str, Any]) -> str:
    # Replace {{key}}, ${key}, $key placeholders with values from mapping.

    result = executor_utils.substitute_variables(template, mapping)
    
    # Then handle ${key} and $key syntax
    for k, v in mapping.items():
        result = (
            result.replace(f"${{{k}}}", str(v))
                  .replace(f"${k}", str(v))
        )
    
    return result


def get_api_key(api_key_id: str, context: ExecutionContext) -> Optional[str]:
    # Get API key from execution context.
    if not hasattr(context, 'api_keys'):
        return None
    
    api_key_info = context.api_keys.get(api_key_id)
    if isinstance(api_key_info, dict):
        return api_key_info.get('key')
    return api_key_info if isinstance(api_key_info, str) else None


def log_action(logger: logging.Logger, node_id: str, action: str, **extra) -> None:
    # Consistent logging helper for node actions.
    log_data = {
        "node_id": node_id,
        "action": action,
        **extra
    }
    logger.info(f"[{node_id}] {action}", extra=log_data)