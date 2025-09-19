"""
Handler module initialization with explicit imports.

This module explicitly imports all handler classes for better traceability
and maintainability.
"""

import logging

# Explicitly import all handler classes
from .api_job import ApiJobNodeHandler
from .code_job import CodeJobNodeHandler
from .codegen.ir_builder import IrBuilderNodeHandler

# Import codegen handlers from their new location for backward compatibility
from .codegen.schema_validator import JsonSchemaValidatorNodeHandler
from .codegen.template import TemplateJobNodeHandler
from .codegen.typescript_ast import TypescriptAstNodeHandler
from .condition import ConditionNodeHandler
from .db import DBTypedNodeHandler
from .endpoint import EndpointNodeHandler
from .hook import HookNodeHandler
from .integrated_api import IntegratedApiNodeHandler
from .person_job import PersonJobNodeHandler
from .start import StartNodeHandler
from .sub_diagram import SubDiagramNodeHandler
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
    "IrBuilderNodeHandler",
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
