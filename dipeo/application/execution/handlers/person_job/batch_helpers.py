"""Batch processing utilities and helper functions."""

from typing import Any

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


def extract_batch_items(inputs: dict[str, Any] | None, batch_input_key: str) -> list[Any]:
    """Extract batch items from inputs, searching nested structures and wrapping non-list values."""
    if not inputs:
        return []

    logger.debug(
        f"Extracting batch items with key '{batch_input_key}' from inputs: {list(inputs.keys())}"
    )

    batch_items = find_batch_items_in_inputs(inputs, batch_input_key)

    if batch_items is None:
        logger.warning(f"No batch items found for key '{batch_input_key}'")
        return []

    if not isinstance(batch_items, list):
        logger.warning(
            f"Batch input '{batch_input_key}' is not a list (type: {type(batch_items)}). "
            f"Treating as single item."
        )
        return [batch_items]

    return batch_items


def find_batch_items_in_inputs(inputs: dict[str, Any], batch_input_key: str) -> Any | None:
    """Find batch items searching root level, 'default' key, and nested dictionaries."""
    if batch_input_key in inputs:
        logger.debug("Found batch items at root level")
        return inputs[batch_input_key]

    if "default" in inputs:
        default_value = inputs["default"]
        if isinstance(default_value, dict) and batch_input_key in default_value:
            logger.debug("Found batch items under 'default'")
            return default_value[batch_input_key]
        if batch_input_key == "default":
            logger.debug("Batch items are the default value itself")
            return default_value
        if isinstance(default_value, dict):
            for key, value in default_value.items():
                if key == batch_input_key:
                    logger.debug(f"Found batch items in default dict at key '{key}'")
                    return value

    return None


def format_item_result(index: int, result: Any) -> dict[str, Any]:
    """Format single item execution result, extracting body from Envelope if present."""
    if hasattr(result, "body"):
        output_value = result.body
        metadata = result.meta if hasattr(result, "meta") else {}
        return {"index": index, "output": output_value, "metadata": metadata}
    else:
        return {"index": index, "output": str(result), "metadata": {}}


def format_batch_error(index: int, error: Exception, batch_items: list[Any]) -> dict[str, Any]:
    """Format error information including index, error details, and failed item."""
    return {
        "index": index,
        "error": str(error),
        "error_type": type(error).__name__,
        "item": batch_items[index] if index < len(batch_items) else None,
    }
