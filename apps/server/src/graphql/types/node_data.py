"""Node data types for different node kinds."""
import strawberry
from typing import Optional, List, Dict, Any
from .scalars import PersonID, ApiKeyID

@strawberry.type
class StartNodeData:
    label: str
    static_data: Optional[Dict[str, Any]] = None

@strawberry.type
class PersonJobNodeData:
    label: str
    prompt: str
    person_id: Optional[PersonID] = None
    first_only_prompt: Optional[str] = None
    merge_consecutive: Optional[bool] = None
    forgetting_options: Optional[Dict[str, Any]] = None
    max_iterations: Optional[int] = None

@strawberry.type
class ConditionNodeData:
    label: str
    condition: str
    fail_on_error: bool = False

@strawberry.type
class JobNodeData:
    label: str
    language: str  # python, javascript, bash
    code: str
    timeout: Optional[int] = None

@strawberry.type
class EndpointNodeData:
    label: str
    operation: str  # save, print, return
    value: Optional[str] = None
    filename: Optional[str] = None

@strawberry.type
class DBNodeData:
    label: str
    operation: str  # save_json, load_json, list_files
    filename: Optional[str] = None
    path: Optional[str] = None
    value: Optional[str] = None

@strawberry.type
class UserResponseNodeData:
    label: str
    prompt: str
    timeout: Optional[int] = None

@strawberry.type
class NotionPageReference:
    page_id: str
    title: Optional[str] = None

@strawberry.type
class NotionNodeData:
    label: str
    operation: str  # read, append, create, update
    api_key_id: ApiKeyID
    page_reference: Optional[NotionPageReference] = None
    content: Optional[str] = None
    parent_page_id: Optional[str] = None
    title: Optional[str] = None

@strawberry.type
class PersonBatchJobNodeData:
    label: str
    prompt: str
    person_id: Optional[PersonID] = None
    parallel: bool = True
    max_concurrency: Optional[int] = None
    batch_size: Optional[int] = None

# Union type for all node data types
NodeDataUnion = strawberry.union("NodeDataUnion", [
    StartNodeData,
    PersonJobNodeData,
    ConditionNodeData,
    JobNodeData,
    EndpointNodeData,
    DBNodeData,
    UserResponseNodeData,
    NotionNodeData,
    PersonBatchJobNodeData
])