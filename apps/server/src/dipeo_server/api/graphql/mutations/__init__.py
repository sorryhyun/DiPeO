from .api_key_mutation import ApiKeyMutations
from .diagram_mutation import DiagramMutations
from .execution_mutation import ExecutionMutations
from .graph_element_mutations import GraphElementMutations
from .node_mutation import NodeMutations
from .person_mutation import PersonMutations
from .upload_mutation import DiagramConvertResult, DiagramSaveResult, UploadMutations
from .utility_mutation import UtilityMutations

__all__ = [
    "ApiKeyMutations",
    "DiagramMutations",
    "ExecutionMutations",
    "GraphElementMutations",
    "NodeMutations",
    "PersonMutations",
    "DiagramConvertResult",
    "DiagramSaveResult",
    "UploadMutations",
    "UtilityMutations",
]


class Mutation:
    pass