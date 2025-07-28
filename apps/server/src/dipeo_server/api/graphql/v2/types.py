"""GraphQL v2 types with interface-based node design."""

import strawberry
from typing import List, Optional
from datetime import datetime
from enum import Enum

# Import existing scalars and enums we'll reuse
from ..types_new import (
    NodeID, DiagramID, ExecutionID, PersonID,
    JSONScalar, Vec2Type, TokenUsageType,
    LLMService as LLMServiceEnum,
)

# Import validation from generated package
from dipeo.diagram_generated.validation.nodes.node_validators import validate_node_data


# ============ Core Types ============

@strawberry.type
class Point:
    """2D position type"""
    x: float
    y: float


# ============ Enums ============

@strawberry.enum
class HttpMethod(Enum):
    """HTTP methods for API calls"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@strawberry.enum
class DBBlockSubType(Enum):
    """Database block sub-types"""
    FIXED_PROMPT = "fixed_prompt"
    FILE = "file"
    CODE = "code"
    API_TOOL = "api_tool"


@strawberry.enum
class AuthType(Enum):
    """Authentication types for API calls"""
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    API_KEY = "api_key"


@strawberry.enum
class TemplateEngine(Enum):
    """Template engine types"""
    INTERNAL = "internal"
    JINJA2 = "jinja2"
    HANDLEBARS = "handlebars"


# ============ Structured Data Types ============

@strawberry.type
class HttpHeader:
    """HTTP header key-value pair"""
    key: str
    value: str


@strawberry.type
class QueryParam:
    """Query parameter key-value pair"""
    key: str
    value: str


@strawberry.type
class AuthConfig:
    """Authentication configuration"""
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    header_name: Optional[str] = None


@strawberry.type
class TemplateVariable:
    """Template variable key-value pair"""
    key: str
    value: JSONScalar


@strawberry.type
class InitialValue:
    """Initial value for diagram execution"""
    key: str
    value: JSONScalar


@strawberry.type
class DBData:
    """Database operation data"""
    fields: Optional[List[JSONScalar]] = None  # Will refine this based on actual usage
    filters: Optional[JSONScalar] = None
    updates: Optional[JSONScalar] = None


# ============ Node Interface & Concrete Types ============

@strawberry.interface
class Node:
    """Base interface for all nodes in a diagram"""
    id: NodeID
    position: Point


@strawberry.type
class PersonNode(Node):
    """AI persona node with LLM configuration"""
    id: NodeID
    position: Point
    
    # Flattened fields - no nested data object
    person_id: PersonID
    model: str
    prompt: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    

@strawberry.type
class CodeNode(Node):
    """Code execution node"""
    id: NodeID
    position: Point
    
    # Flattened fields
    language: str
    code: str
    timeout_seconds: Optional[int] = 30
    

@strawberry.type
class StartNode(Node):
    """Entry point node for diagram execution"""
    id: NodeID
    position: Point
    
    # Start nodes have minimal data
    initial_values: Optional[List[InitialValue]] = None


@strawberry.type
class ConditionNode(Node):
    """Conditional branching node"""
    id: NodeID
    position: Point
    
    # Flattened fields
    condition_type: str
    expression: Optional[str] = None
    node_indices: Optional[List[str]] = None


@strawberry.type
class ApiJobNode(Node):
    """HTTP API request node"""
    id: NodeID
    position: Point
    
    # Flattened fields
    url: str
    method: HttpMethod
    headers: Optional[List[HttpHeader]] = None
    params: Optional[List[QueryParam]] = None
    body: Optional[JSONScalar] = None  # Body can remain flexible as JSON
    timeout: Optional[int] = None
    auth_type: Optional[AuthType] = None
    auth_config: Optional[AuthConfig] = None


@strawberry.type
class TemplateJobNode(Node):
    """Template processing node"""
    id: NodeID
    position: Point
    
    # Flattened fields
    template_path: Optional[str] = None
    template_content: Optional[str] = None
    output_path: Optional[str] = None
    variables: Optional[List[TemplateVariable]] = None
    engine: Optional[TemplateEngine] = None


@strawberry.type
class DBNode(Node):
    """Database operations node"""
    id: NodeID
    position: Point
    
    # Flattened fields
    file: Optional[str] = None
    collection: Optional[str] = None
    sub_type: DBBlockSubType
    operation: str
    query: Optional[str] = None
    data: Optional[DBData] = None


@strawberry.type
class UserResponseNode(Node):
    """User input collection node"""
    id: NodeID
    position: Point
    
    # Flattened fields
    prompt: str
    timeout: int


# ============ Input Types ============

@strawberry.input
class PointInput:
    """Input type for 2D position"""
    x: float
    y: float


@strawberry.input
class HttpHeaderInput:
    """Input for HTTP header key-value pair"""
    key: str
    value: str


@strawberry.input
class QueryParamInput:
    """Input for query parameter key-value pair"""
    key: str
    value: str


@strawberry.input
class AuthConfigInput:
    """Input for authentication configuration"""
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    header_name: Optional[str] = None


@strawberry.input
class TemplateVariableInput:
    """Input for template variable key-value pair"""
    key: str
    value: JSONScalar


@strawberry.input
class InitialValueInput:
    """Input for initial value"""
    key: str
    value: JSONScalar


@strawberry.input
class DBDataInput:
    """Input for database operation data"""
    fields: Optional[List[JSONScalar]] = None
    filters: Optional[JSONScalar] = None
    updates: Optional[JSONScalar] = None


@strawberry.input
class CreatePersonNodeInput:
    """Input for creating a PersonNode"""
    position: PointInput
    person_id: PersonID
    model: str
    prompt: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None


@strawberry.input
class CreateCodeNodeInput:
    """Input for creating a CodeNode"""
    position: PointInput
    language: str
    code: str
    timeout_seconds: Optional[int] = 30


@strawberry.input
class CreateStartNodeInput:
    """Input for creating a StartNode"""
    position: PointInput
    initial_values: Optional[List[InitialValueInput]] = None


@strawberry.input
class CreateConditionNodeInput:
    """Input for creating a ConditionNode"""
    position: PointInput
    condition_type: str
    expression: Optional[str] = None
    node_indices: Optional[List[str]] = None


@strawberry.input
class CreateApiJobNodeInput:
    """Input for creating an ApiJobNode"""
    position: PointInput
    url: str
    method: HttpMethod
    headers: Optional[List[HttpHeaderInput]] = None
    params: Optional[List[QueryParamInput]] = None
    body: Optional[JSONScalar] = None
    timeout: Optional[int] = None
    auth_type: Optional[AuthType] = None
    auth_config: Optional[AuthConfigInput] = None


@strawberry.input
class CreateTemplateJobNodeInput:
    """Input for creating a TemplateJobNode"""
    position: PointInput
    template_path: Optional[str] = None
    template_content: Optional[str] = None
    output_path: Optional[str] = None
    variables: Optional[List[TemplateVariableInput]] = None
    engine: Optional[TemplateEngine] = None


@strawberry.input
class CreateDBNodeInput:
    """Input for creating a DBNode"""
    position: PointInput
    file: Optional[str] = None
    collection: Optional[str] = None
    sub_type: DBBlockSubType
    operation: str
    query: Optional[str] = None
    data: Optional[DBDataInput] = None


@strawberry.input
class CreateUserResponseNodeInput:
    """Input for creating a UserResponseNode"""
    position: PointInput
    prompt: str
    timeout: int


# ============ Results ============

@strawberry.type
class PersonNodeResult:
    """Result of PersonNode operations"""
    success: bool
    node: Optional[PersonNode] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class CodeNodeResult:
    """Result of CodeNode operations"""
    success: bool
    node: Optional[CodeNode] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class StartNodeResult:
    """Result of StartNode operations"""
    success: bool
    node: Optional[StartNode] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class ConditionNodeResult:
    """Result of ConditionNode operations"""
    success: bool
    node: Optional[ConditionNode] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class ApiJobNodeResult:
    """Result of ApiJobNode operations"""
    success: bool
    node: Optional[ApiJobNode] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class TemplateJobNodeResult:
    """Result of TemplateJobNode operations"""
    success: bool
    node: Optional[TemplateJobNode] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class DBNodeResult:
    """Result of DBNode operations"""
    success: bool
    node: Optional[DBNode] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class UserResponseNodeResult:
    """Result of UserResponseNode operations"""
    success: bool
    node: Optional[UserResponseNode] = None
    message: Optional[str] = None
    error: Optional[str] = None


# ============ Diagram Type ============

@strawberry.type
class Diagram:
    """Diagram containing nodes and connections"""
    id: DiagramID
    name: str
    description: Optional[str]
    nodes: List[Node]  # Polymorphic list using interface
    created_at: datetime
    updated_at: datetime


# ============ Query, Mutation, Subscription ============

@strawberry.type
class Query:
    """GraphQL v2 queries"""
    
    @strawberry.field
    async def diagram(self, id: DiagramID) -> Optional[Diagram]:
        """Get a diagram by ID"""
        # TODO: Implement resolver
        return None
    
    @strawberry.field
    async def node(self, id: NodeID) -> Optional[Node]:
        """Get a node by ID - returns interface type"""
        # TODO: Implement resolver
        return None


@strawberry.type
class Mutation:
    """GraphQL v2 mutations - per-node type for maximum type safety"""
    
    @strawberry.mutation
    async def create_person_node(
        self, 
        diagram_id: DiagramID,
        input: CreatePersonNodeInput
    ) -> PersonNodeResult:
        """Create a new PersonNode"""
        try:
            # Validate input using Pydantic
            input_dict = {
                "position": {"x": input.position.x, "y": input.position.y},
                "person_id": input.person_id,
                "model": input.model,
                "prompt": input.prompt,
                "temperature": input.temperature,
                "max_tokens": input.max_tokens,
                "system_prompt": input.system_prompt
            }
            
            validated_data = validate_node_data("personjob", input_dict)
            
            # TODO: Implement actual node creation with database persistence
            # For now, return a mock success response
            node = PersonNode(
                id=NodeID("mock-node-id"),
                position=Point(x=input.position.x, y=input.position.y),
                person_id=input.person_id,
                model=input.model,
                prompt=input.prompt,
                temperature=input.temperature,
                max_tokens=input.max_tokens,
                system_prompt=input.system_prompt
            )
            
            return PersonNodeResult(
                success=True,
                node=node,
                message="PersonNode created successfully (mock)"
            )
            
        except ValueError as e:
            return PersonNodeResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            return PersonNodeResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    @strawberry.mutation
    async def create_code_node(
        self,
        diagram_id: DiagramID, 
        input: CreateCodeNodeInput
    ) -> CodeNodeResult:
        """Create a new CodeNode"""
        try:
            # Validate input using Pydantic
            input_dict = {
                "position": {"x": input.position.x, "y": input.position.y},
                "language": input.language,
                "code": input.code,
                "timeout_seconds": input.timeout_seconds
            }
            
            validated_data = validate_node_data("codejob", input_dict)
            
            # TODO: Implement actual node creation with database persistence
            # For now, return a mock success response
            node = CodeNode(
                id=NodeID("mock-code-node-id"),
                position=Point(x=input.position.x, y=input.position.y),
                language=input.language,
                code=input.code,
                timeout_seconds=input.timeout_seconds
            )
            
            return CodeNodeResult(
                success=True,
                node=node,
                message="CodeNode created successfully (mock)"
            )
            
        except ValueError as e:
            return CodeNodeResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            return CodeNodeResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    @strawberry.mutation
    async def create_start_node(
        self,
        diagram_id: DiagramID,
        input: CreateStartNodeInput
    ) -> StartNodeResult:
        """Create a new StartNode"""
        # TODO: Implement with Pydantic validation
        return StartNodeResult(
            success=False,
            message="Not implemented yet"
        )
    
    @strawberry.mutation
    async def create_condition_node(
        self,
        diagram_id: DiagramID,
        input: CreateConditionNodeInput
    ) -> ConditionNodeResult:
        """Create a new ConditionNode"""
        # TODO: Implement with Pydantic validation
        return ConditionNodeResult(
            success=False,
            message="Not implemented yet"
        )
    
    @strawberry.mutation
    async def create_api_job_node(
        self,
        diagram_id: DiagramID,
        input: CreateApiJobNodeInput
    ) -> ApiJobNodeResult:
        """Create a new ApiJobNode"""
        try:
            # Convert structured types to dict format for validation
            input_dict = {
                "position": {"x": input.position.x, "y": input.position.y},
                "url": input.url,
                "method": input.method.value,
                "headers": [{"key": h.key, "value": h.value} for h in (input.headers or [])],
                "params": [{"key": p.key, "value": p.value} for p in (input.params or [])],
                "body": input.body,
                "timeout": input.timeout,
                "auth_type": input.auth_type.value if input.auth_type else None,
                "auth_config": {
                    "token": input.auth_config.token,
                    "username": input.auth_config.username,
                    "password": input.auth_config.password,
                    "api_key": input.auth_config.api_key,
                    "header_name": input.auth_config.header_name
                } if input.auth_config else None
            }
            
            validated_data = validate_node_data("apijob", input_dict)
            
            # TODO: Implement actual node creation with database persistence
            # For now, return a mock success response
            node = ApiJobNode(
                id=NodeID("mock-api-node-id"),
                position=Point(x=input.position.x, y=input.position.y),
                url=input.url,
                method=input.method,
                headers=[HttpHeader(key=h.key, value=h.value) for h in (input.headers or [])],
                params=[QueryParam(key=p.key, value=p.value) for p in (input.params or [])],
                body=input.body,
                timeout=input.timeout,
                auth_type=input.auth_type,
                auth_config=AuthConfig(
                    token=input.auth_config.token,
                    username=input.auth_config.username,
                    password=input.auth_config.password,
                    api_key=input.auth_config.api_key,
                    header_name=input.auth_config.header_name
                ) if input.auth_config else None
            )
            
            return ApiJobNodeResult(
                success=True,
                node=node,
                message="ApiJobNode created successfully (mock)"
            )
            
        except ValueError as e:
            return ApiJobNodeResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            return ApiJobNodeResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    @strawberry.mutation
    async def create_template_job_node(
        self,
        diagram_id: DiagramID,
        input: CreateTemplateJobNodeInput
    ) -> TemplateJobNodeResult:
        """Create a new TemplateJobNode"""
        # TODO: Implement with Pydantic validation
        return TemplateJobNodeResult(
            success=False,
            message="Not implemented yet"
        )
    
    @strawberry.mutation
    async def create_db_node(
        self,
        diagram_id: DiagramID,
        input: CreateDBNodeInput
    ) -> DBNodeResult:
        """Create a new DBNode"""
        # TODO: Implement with Pydantic validation
        return DBNodeResult(
            success=False,
            message="Not implemented yet"
        )
    
    @strawberry.mutation
    async def create_user_response_node(
        self,
        diagram_id: DiagramID,
        input: CreateUserResponseNodeInput
    ) -> UserResponseNodeResult:
        """Create a new UserResponseNode"""
        # TODO: Implement with Pydantic validation
        return UserResponseNodeResult(
            success=False,
            message="Not implemented yet"
        )


@strawberry.type
class Subscription:
    """GraphQL v2 subscriptions"""
    
    @strawberry.subscription
    async def placeholder(self) -> str:
        """Placeholder subscription - will implement execution updates later"""
        import asyncio
        while True:
            yield "v2 subscription placeholder"
            await asyncio.sleep(5)