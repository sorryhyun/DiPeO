"""
Handler module initialization with explicit imports.

This module explicitly imports all handler classes for better traceability
and maintainability.
"""

import logging

# Explicitly import all handler classes
from .api_job import ApiJobNodeHandler
from .code_job import CodeJobNodeHandler
from .condition import ConditionNodeHandler
from .db import DBTypedNodeHandler
from .endpoint import EndpointNodeHandler
from .hook import HookNodeHandler
from .integrated_api import IntegratedApiNodeHandler
from .json_schema_validator import JsonSchemaValidatorNodeHandler
from .person_job import PersonJobNodeHandler
from .start import StartNodeHandler
from .sub_diagram import SubDiagramNodeHandler
from .template_job import TemplateJobNodeHandler
from .typescript_ast import TypescriptAstNodeHandler
from .user_response import UserResponseNodeHandler

# Export all handler classes
__all__ = [
    "ApiJobNodeHandler",
    "CodeJobNodeHandler",
    "ConditionNodeHandler",
    "DBTypedNodeHandler",
    "EndpointNodeHandler",
    "HookNodeHandler",
    "IntegratedApiNodeHandler",
    "JsonSchemaValidatorNodeHandler",
    "PersonJobNodeHandler",
    "StartNodeHandler",
    "SubDiagramNodeHandler",
    "TemplateJobNodeHandler",
    "TypescriptAstNodeHandler",
    "UserResponseNodeHandler",
]

logger = logging.getLogger(__name__)
logger.info(f"✅ Loaded {len(__all__)} handlers")
