"""
Handler module initialization with explicit imports.

This module explicitly imports all handler classes for better traceability
and maintainability.
"""

import logging

logger = logging.getLogger(__name__)

# Explicitly import all handler classes
from .start import StartNodeHandler
from .person_job import PersonJobNodeHandler
from .code_job import CodeJobNodeHandler
from .condition import ConditionNodeHandler
from .api_job import ApiJobNodeHandler
from .endpoint import EndpointNodeHandler
from .db import DBTypedNodeHandler
from .user_response import UserResponseNodeHandler
from .hook import HookNodeHandler
from .template_job import TemplateJobNodeHandler
from .json_schema_validator import JsonSchemaValidatorNodeHandler
from .typescript_ast import TypescriptAstNodeHandler
from .sub_diagram import SubDiagramNodeHandler
from .integrated_api import IntegratedApiNodeHandler

# Export all handler classes
__all__ = [
    "StartNodeHandler",
    "PersonJobNodeHandler",
    "CodeJobNodeHandler",
    "ConditionNodeHandler",
    "ApiJobNodeHandler",
    "EndpointNodeHandler",
    "DBTypedNodeHandler",
    "UserResponseNodeHandler",
    "HookNodeHandler",
    "TemplateJobNodeHandler",
    "JsonSchemaValidatorNodeHandler",
    "TypescriptAstNodeHandler",
    "SubDiagramNodeHandler",
    "IntegratedApiNodeHandler",
]

logger.info(f"✅ Loaded {len(__all__)} handlers")