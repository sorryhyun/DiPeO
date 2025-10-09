"""Shared utility modules for handlers."""

from dipeo.application.execution.handlers.utils.envelope_helpers import (
    create_batch_result_body,
    create_error_body,
    create_operation_result_body,
    create_text_result_body,
)
from dipeo.application.execution.handlers.utils.input_helpers import (
    extract_content_value,
    extract_first_non_empty,
    get_input_by_priority,
    prepare_template_values,
)
from dipeo.application.execution.handlers.utils.serialization import (
    deserialize_data,
    serialize_data,
)
from dipeo.application.execution.handlers.utils.service_helpers import (
    has_service,
    normalize_service_key,
    resolve_optional_service,
    resolve_required_service,
)
from dipeo.application.execution.handlers.utils.state_helpers import (
    get_all_node_results,
    get_node_execution_count,
    get_node_result,
    get_node_status,
    has_node_executed,
    is_node_completed,
)
from dipeo.application.execution.handlers.utils.validation_helpers import (
    validate_config_field,
    validate_file_paths,
    validate_operation,
    validate_required_field,
)

__all__ = [
    # Envelope helpers
    "create_batch_result_body",
    "create_error_body",
    "create_operation_result_body",
    "create_text_result_body",
    # Serialization
    "deserialize_data",
    # Input helpers
    "extract_content_value",
    "extract_first_non_empty",
    # State helpers
    "get_all_node_results",
    "get_input_by_priority",
    "get_node_execution_count",
    "get_node_result",
    "get_node_status",
    "has_node_executed",
    # Service helpers
    "has_service",
    "is_node_completed",
    "normalize_service_key",
    "prepare_template_values",
    "resolve_optional_service",
    "resolve_required_service",
    "serialize_data",
    # Validation helpers
    "validate_config_field",
    "validate_file_paths",
    "validate_operation",
    "validate_required_field",
]
