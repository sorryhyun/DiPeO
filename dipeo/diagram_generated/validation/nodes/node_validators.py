# Combined node validators for GraphQL v2
from typing import Type

from pydantic import BaseModel

# Import all node models
from .apijob_models import Model as ApijobNodeData
from .codejob_models import Model as CodejobNodeData
from .condition_models import Model as ConditionNodeData
from .db_models import Model as DbNodeData
from .endpoint_models import Model as EndpointNodeData
from .hook_models import Model as HookNodeData
from .jsonschemavalidator_models import Model as JsonschemavalidatorNodeData
from .personbatchjob_models import Model as PersonbatchjobNodeData
from .personjob_models import Model as PersonjobNodeData
from .start_models import Model as StartNodeData
from .subdiagram_models import Model as SubdiagramNodeData
from .templatejob_models import Model as TemplatejobNodeData
from .typescriptast_models import Model as TypescriptastNodeData
from .userresponse_models import Model as UserresponseNodeData

# Validator mapping
NODE_VALIDATORS: dict[str, type[BaseModel]] = {
    "apijob": ApijobNodeData,
    "codejob": CodejobNodeData,
    "condition": ConditionNodeData,
    "db": DbNodeData,
    "endpoint": EndpointNodeData,
    "hook": HookNodeData,
    "jsonschemavalidator": JsonschemavalidatorNodeData,
    "personbatchjob": PersonbatchjobNodeData,
    "personjob": PersonjobNodeData,
    "start": StartNodeData,
    "subdiagram": SubdiagramNodeData,
    "templatejob": TemplatejobNodeData,
    "typescriptast": TypescriptastNodeData,
    "userresponse": UserresponseNodeData,
}

def validate_node_data(node_type: str, data: dict) -> BaseModel:
    """Validate node data against its schema."""
    validator_class = NODE_VALIDATORS.get(node_type)
    if not validator_class:
        raise ValueError(f"No validator found for node type: {node_type}")

    return validator_class(**data)
