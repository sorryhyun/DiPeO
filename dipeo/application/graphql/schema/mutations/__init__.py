"""GraphQL mutations organized by domain."""

from .diagram import create_diagram_mutations
from .execution import create_execution_mutations
from .person import create_person_mutations
from .api_key import create_api_key_mutations
from .node import create_node_mutations
from .upload import create_upload_mutations
from .cli_session import create_cli_session_mutations

__all__ = [
    "create_diagram_mutations",
    "create_execution_mutations", 
    "create_person_mutations",
    "create_api_key_mutations",
    "create_node_mutations",
    "create_upload_mutations",
    "create_cli_session_mutations",
]