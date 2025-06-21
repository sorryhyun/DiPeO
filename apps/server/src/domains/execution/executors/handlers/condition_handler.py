from __future__ import annotations

import logging
import time
from typing import Any, Dict

from ..decorators import node
from ..schemas.condition import ConditionNodeProps, ConditionType
from ..types import ExecutionContext
from ..utils.handler_utils import safe_eval
from src.__generated__.models import NodeOutput

logger = logging.getLogger(__name__)


@node(
    node_type="condition",
    schema=ConditionNodeProps,
    description="Conditional branching based on boolean expression evaluation",
)
async def condition_handler(
    props: ConditionNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any],
    services: Dict[str, Any] | None = None,
) -> NodeOutput:
    """Evaluate the configured condition and return a boolean result."""

    try:
        result = (
            _check_max_iterations(context)
            if props.conditionType == ConditionType.DETECT_MAX_ITERATIONS
            else safe_eval(props.expression or "False", inputs, context)
        )
        error: str | None = None
    except Exception as exc:  # pragma: no cover
        logger.exception("Condition evaluation failed: %s", exc)
        result = False
        error = str(exc)

    return NodeOutput(
        value=result,
        metadata={
            "conditionType": props.conditionType.value if props.conditionType else None,
            "expression": props.expression,
            "evaluatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **({"error": error} if error else {}),
        },
    )


# Helpers


def _check_max_iterations(ctx: ExecutionContext) -> bool:
    """Placeholder for DETECT_MAX_ITERATIONS condition (not yet implemented)."""
    logger.warning("DETECT_MAX_ITERATIONS is not yet supported; returning False")
    return False
