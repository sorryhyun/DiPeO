"""Application layer handlers for orchestrating node execution.

These handlers coordinate between multiple domain services to execute nodes
in the diagram. They are part of the application layer, not the domain layer,
as they orchestrate across multiple domains.
"""

from .condition import ConditionNodeHandler
from .db import DBNodeHandler
from .endpoint import EndpointNodeHandler
from .job import JobNodeHandler
from .notion import NotionNodeHandler
from .person_batch_job import PersonBatchJobNodeHandler
from .person_job import PersonJobNodeHandler
from .start import StartNodeHandler
from .user_response import UserResponseNodeHandler

__all__ = [
    "ConditionNodeHandler",
    "DBNodeHandler",
    "EndpointNodeHandler",
    "JobNodeHandler",
    "NotionNodeHandler",
    "PersonBatchJobNodeHandler",
    "PersonJobNodeHandler",
    "StartNodeHandler",
    "UserResponseNodeHandler",
]


# Legacy compatibility - handlers are auto-registered via @register_handler
def register_all_handlers(registry):
    """Legacy function - handlers are now auto-registered."""
    pass
