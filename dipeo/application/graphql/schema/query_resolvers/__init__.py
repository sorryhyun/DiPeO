"""Query resolver functions organized by domain."""

from .api_keys import get_api_key, get_api_keys, get_available_models
from .cli_sessions import get_active_cli_session
from .diagrams import get_diagram, list_diagrams
from .executions import (
    get_execution,
    get_execution_history,
    get_execution_metrics,
    get_execution_order,
    list_executions,
)
from .persons import get_person, list_persons
from .prompts import get_prompt_file, list_prompt_files
from .providers import (
    get_operation_schema,
    get_provider,
    get_provider_operations,
    get_provider_statistics,
    get_providers,
)
from .system import get_execution_capabilities, get_system_info, health_check, list_conversations

__all__ = [
    # CLI Sessions
    "get_active_cli_session",
    # API Keys
    "get_api_key",
    "get_api_keys",
    "get_available_models",
    # Diagrams
    "get_diagram",
    # Executions
    "get_execution",
    "get_execution_capabilities",
    "get_execution_history",
    "get_execution_metrics",
    "get_execution_order",
    "get_operation_schema",
    # Persons
    "get_person",
    "get_prompt_file",
    "get_provider",
    "get_provider_operations",
    "get_provider_statistics",
    # Providers
    "get_providers",
    # System
    "get_system_info",
    "health_check",
    "list_conversations",
    "list_diagrams",
    "list_executions",
    "list_persons",
    # Prompts
    "list_prompt_files",
]
