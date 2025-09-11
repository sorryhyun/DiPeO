"""
DO NOT EDIT - Generated from TypeScript query definitions

Generated from TypeScript query definitions in dipeo/models/src/frontend/query-definitions/
Total operations: 45 (23 queries, 21 mutations, 1 subscriptions)
"""

from typing import Any, Optional, TypedDict, Protocol, Union
import strawberry
from typing import Any, Optional, TypedDict, Union
from dipeo.diagram_generated.graphql.inputs import CreateApiKeyInput, CreateDiagramInput, CreateNodeInput, CreatePersonInput, DiagramFilterInput, ExecuteDiagramInput, ExecutionControlInput, ExecutionFilterInput, InteractiveResponseInput, RegisterCliSessionInput, UnregisterCliSessionInput, UpdateNodeInput, UpdateNodeStateInput, UpdatePersonInput
from dipeo.diagram_generated.enums import DiagramFormat


# GraphQL query strings as constants

CONTROL_EXECUTION_MUTATION = """mutation ControlExecution($input: ExecutionControlInput!) {
  control_execution(input: $input) {
    success
    execution_id
    execution {
      id
      status
    }
    message
    error
  }
}"""



CONVERT_DIAGRAM_FORMAT_MUTATION = """mutation ConvertDiagramFormat($content: String!, $from_format: DiagramFormat!, $to_format: DiagramFormat!) {
  convert_diagram_format(content: $content, from_format: $from_format, to_format: $to_format) {
    success
    content
    format
    message
    error
  }
}"""



CREATE_API_KEY_MUTATION = """mutation CreateApiKey($input: CreateApiKeyInput!) {
  create_api_key(input: $input) {
    success
    api_key {
      id
      label
      service
    }
    message
    error
  }
}"""



CREATE_DIAGRAM_MUTATION = """mutation CreateDiagram($input: CreateDiagramInput!) {
  create_diagram(input: $input) {
    success
    diagram {
      metadata {
        id
        name
      }
    }
    message
    error
  }
}"""



CREATE_NODE_MUTATION = """mutation CreateNode($diagram_id: ID!, $input: CreateNodeInput!) {
  create_node(diagram_id: $diagram_id, input: $input) {
    success
    node {
      id
      type
      position {
        x
        y
      }
      data
    }
    message
    error
  }
}"""



CREATE_PERSON_MUTATION = """mutation CreatePerson($input: CreatePersonInput!) {
  create_person(input: $input) {
    success
    person {
      id
      label
    }
    message
    error
  }
}"""



DELETE_API_KEY_MUTATION = """mutation DeleteApiKey($id: ID!) {
  delete_api_key(id: $id) {
    success
    message
  }
}"""



DELETE_DIAGRAM_MUTATION = """mutation DeleteDiagram($id: ID!) {
  delete_diagram(id: $id) {
    success
    message
    error
  }
}"""



DELETE_NODE_MUTATION = """mutation DeleteNode($diagram_id: ID!, $node_id: ID!) {
  delete_node(diagram_id: $diagram_id, node_id: $node_id) {
    success
    message
    error
  }
}"""



DELETE_PERSON_MUTATION = """mutation DeletePerson($id: ID!) {
  delete_person(id: $id) {
    success
    message
    error
  }
}"""



EXECUTE_DIAGRAM_MUTATION = """mutation ExecuteDiagram($input: ExecuteDiagramInput!) {
  execute_diagram(input: $input) {
    success
    execution {
      id
    }
    message
    error
  }
}"""



REGISTER_CLI_SESSION_MUTATION = """mutation RegisterCliSession($input: RegisterCliSessionInput!) {
  register_cli_session(input: $input) {
    success
    message
    error
  }
}"""



SEND_INTERACTIVE_RESPONSE_MUTATION = """mutation SendInteractiveResponse($input: InteractiveResponseInput!) {
  send_interactive_response(input: $input) {
    success
    execution_id
    message
    error
  }
}"""



TEST_API_KEY_MUTATION = """mutation TestApiKey($id: ID!) {
  test_api_key(id: $id) {
    success
    message
    error
  }
}"""



UNREGISTER_CLI_SESSION_MUTATION = """mutation UnregisterCliSession($input: UnregisterCliSessionInput!) {
  unregister_cli_session(input: $input) {
    success
    message
    error
  }
}"""



UPDATE_NODE_MUTATION = """mutation UpdateNode($diagram_id: ID!, $node_id: ID!, $input: UpdateNodeInput!) {
  update_node(diagram_id: $diagram_id, node_id: $node_id, input: $input) {
    success
    message
    error
  }
}"""



UPDATE_NODE_STATE_MUTATION = """mutation UpdateNodeState($input: UpdateNodeStateInput!) {
  update_node_state(input: $input) {
    success
    execution_id
    execution {
      id
      status
    }
    message
    error
  }
}"""



UPDATE_PERSON_MUTATION = """mutation UpdatePerson($id: ID!, $input: UpdatePersonInput!) {
  update_person(id: $id, input: $input) {
    success
    person {
      id
      label
    }
    message
    error
  }
}"""



UPLOAD_DIAGRAM_MUTATION = """mutation UploadDiagram($file: Upload!, $format: DiagramFormat!) {
  upload_diagram(file: $file, format: $format) {
    success
    diagram {
      metadata {
        id
        name
      }
    }
    message
    error
  }
}"""



UPLOAD_FILE_MUTATION = """mutation UploadFile($file: Upload!, $path: String) {
  upload_file(file: $file, path: $path) {
    success
    path
    size_bytes
    content_type
    message
    error
  }
}"""



VALIDATE_DIAGRAM_MUTATION = """mutation ValidateDiagram($content: String!, $format: DiagramFormat!) {
  validate_diagram(content: $content, format: $format) {
    success
    errors
    warnings
    message
  }
}"""



GET_ACTIVE_CLI_SESSION_QUERY = """query GetActiveCliSession {
  active_cli_session {
    session_id
    execution_id
    diagram_name
    diagram_format
    started_at
    is_active
    diagram_data
    node_states
  }
}"""



GET_API_KEY_QUERY = """query GetApiKey($id: ID!) {
  api_key(id: $id) {
    id
    label
    service
  }
}"""



GET_API_KEYS_QUERY = """query GetApiKeys($service: String) {
  api_keys(service: $service) {
    id
    label
    service
    key
  }
}"""



GET_AVAILABLE_MODELS_QUERY = """query GetAvailableModels($service: String!, $apiKeyId: ID!) {
  available_models(service: $service, api_key_id: $apiKeyId)
}"""



GET_DIAGRAM_QUERY = """query GetDiagram($id: ID!) {
  diagram(id: $id) {
    nodes {
      id
      type
      position {
        x
        y
      }
      data
    }
    handles {
      id
      node_id
      label
      direction
      data_type
      position
    }
    arrows {
      id
      source
      target
      content_type
      label
      data
    }
    persons {
      id
      label
      llm_config {
        service
        model
        api_key_id
        system_prompt
      }
      type
    }
    metadata {
      id
      name
      description
      version
      created
      modified
      author
      tags
    }
  }
}"""



GET_EXECUTION_QUERY = """query GetExecution($id: ID!) {
  execution(id: $id) {
    id
    status
    diagram_id
    started_at
    ended_at
    error
    node_states
    node_outputs
    variables
    metrics
  }
}"""



GET_EXECUTION_CAPABILITIES_QUERY = """query GetExecutionCapabilities {
  execution_capabilities
}"""



GET_EXECUTION_HISTORY_QUERY = """query GetExecutionHistory($diagram_id: ID, $limit: Int, $include_metrics: Boolean) {
  execution_history {
    id
    status
    diagram_id
    started_at
    ended_at
    error
    metrics
  }
}"""



GET_EXECUTION_METRICS_QUERY = """query GetExecutionMetrics($execution_id: ID!) {
  execution_metrics(execution_id: $execution_id)
}"""



GET_EXECUTION_ORDER_QUERY = """query GetExecutionOrder($execution_id: ID!) {
  execution_order(execution_id: $execution_id)
}"""



GET_OPERATION_SCHEMA_QUERY = """query GetOperationSchema($provider: String!, $operation: String!) {
  operation_schema(provider: $provider, operation: $operation) {
    operation
    method
    path
    description
    request_body
    query_params
    response
  }
}"""



GET_PERSON_QUERY = """query GetPerson($id: ID!) {
  person(id: $id) {
    id
    label
    type
    llm_config {
      service
      model
      api_key_id
      system_prompt
    }
  }
}"""



GET_PROMPT_FILE_QUERY = """query GetPromptFile($filename: String!) {
  prompt_file(filename: $filename)
}"""



GET_PROVIDER_OPERATIONS_QUERY = """query GetProviderOperations($provider: String!) {
  provider_operations(provider: $provider) {
    name
    method
    path
    description
    required_scopes
    has_pagination
    timeout_override
  }
}"""



GET_PROVIDERS_QUERY = """query GetProviders {
  providers {
    name
    operations {
      name
      method
      path
      description
      required_scopes
    }
    metadata {
      version
      type
      description
      documentation_url
    }
    base_url
    default_timeout
  }
}"""



GET_SUPPORTED_FORMATS_QUERY = """query GetSupportedFormats {
  supported_formats {
    format
    name
    description
    extension
    supports_import
    supports_export
  }
}"""



GET_SYSTEM_INFO_QUERY = """query GetSystemInfo {
  system_info
}"""



HEALTH_CHECK_QUERY = """query HealthCheck {
  health
}"""



LIST_CONVERSATIONS_QUERY = """query ListConversations($person_id: ID, $execution_id: ID, $search: String, $show_forgotten: Boolean, $limit: Int, $offset: Int, $since: DateTime) {
  conversations(person_id: $person_id, execution_id: $execution_id, search: $search, show_forgotten: $show_forgotten, limit: $limit, offset: $offset, since: $since)
}"""



LIST_DIAGRAMS_QUERY = """query ListDiagrams($filter: DiagramFilterInput, $limit: Int, $offset: Int) {
  diagrams(filter: $filter, limit: $limit, offset: $offset) {
    metadata {
      id
      name
      description
      author
      created
      modified
      tags
    }
    nodeCount
    arrowCount
  }
}"""



LIST_EXECUTIONS_QUERY = """query ListExecutions($filter: ExecutionFilterInput, $limit: Int, $offset: Int) {
  executions(filter: $filter, limit: $limit, offset: $offset) {
    id
    status
    diagram_id
    started_at
    ended_at
    error
  }
}"""



LIST_PERSONS_QUERY = """query ListPersons($limit: Int) {
  persons(limit: $limit) {
    id
    label
    type
    llm_config {
      service
      model
      api_key_id
    }
  }
}"""



LIST_PROMPT_FILES_QUERY = """query ListPromptFiles {
  prompt_files
}"""



EXECUTION_UPDATES_SUBSCRIPTION = """subscription ExecutionUpdates($execution_id: ID!) {
  execution_updates(execution_id: $execution_id) {
    execution_id
    event_type
    data
    timestamp
  }
}"""



# Typed operation classes


class ControlExecutionOperation:
    """
    Mutation operation for Execution.
    GraphQL mutation: ControlExecution
    """
    
    query = CONTROL_EXECUTION_MUTATION
    operation_type = "mutation"
    operation_name = "ControlExecution"
    
    
    class Variables(TypedDict):
        """Variable types for ControlExecution mutation."""
        
        input: ExecutionControlInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, input: Union[ExecutionControlInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            input: ExecutionControlInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class ConvertDiagramFormatOperation:
    """
    Mutation operation for File.
    GraphQL mutation: ConvertDiagramFormat
    """
    
    query = CONVERT_DIAGRAM_FORMAT_MUTATION
    operation_type = "mutation"
    operation_name = "ConvertDiagramFormat"
    
    
    class Variables(TypedDict):
        """Variable types for ConvertDiagramFormat mutation."""
        
        content: str
        
        from_format: DiagramFormat
        
        to_format: DiagramFormat
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, content: str, from_format: DiagramFormat, to_format: DiagramFormat) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            content: String - Required (accepts dict or Strawberry input object)
            
            from_format: DiagramFormat - Required (accepts dict or Strawberry input object)
            
            to_format: DiagramFormat - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(content, '__strawberry_definition__'):
            variables["content"] = strawberry.asdict(content)
        else:
            variables["content"] = content
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(from_format, '__strawberry_definition__'):
            variables["from_format"] = strawberry.asdict(from_format)
        else:
            variables["from_format"] = from_format
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(to_format, '__strawberry_definition__'):
            variables["to_format"] = strawberry.asdict(to_format)
        else:
            variables["to_format"] = to_format
        
        
        return variables


class CreateApiKeyOperation:
    """
    Mutation operation for ApiKey.
    GraphQL mutation: CreateApiKey
    """
    
    query = CREATE_API_KEY_MUTATION
    operation_type = "mutation"
    operation_name = "CreateApiKey"
    
    
    class Variables(TypedDict):
        """Variable types for CreateApiKey mutation."""
        
        input: CreateApiKeyInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, input: Union[CreateApiKeyInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            input: CreateApiKeyInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class CreateDiagramOperation:
    """
    Mutation operation for Diagram.
    GraphQL mutation: CreateDiagram
    """
    
    query = CREATE_DIAGRAM_MUTATION
    operation_type = "mutation"
    operation_name = "CreateDiagram"
    
    
    class Variables(TypedDict):
        """Variable types for CreateDiagram mutation."""
        
        input: CreateDiagramInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, input: Union[CreateDiagramInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            input: CreateDiagramInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class CreateNodeOperation:
    """
    Mutation operation for Node.
    GraphQL mutation: CreateNode
    """
    
    query = CREATE_NODE_MUTATION
    operation_type = "mutation"
    operation_name = "CreateNode"
    
    
    class Variables(TypedDict):
        """Variable types for CreateNode mutation."""
        
        diagram_id: str
        
        input: CreateNodeInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, diagram_id: str, input: Union[CreateNodeInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            diagram_id: ID - Required (accepts dict or Strawberry input object)
            
            input: CreateNodeInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(diagram_id, '__strawberry_definition__'):
            variables["diagram_id"] = strawberry.asdict(diagram_id)
        else:
            variables["diagram_id"] = diagram_id
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class CreatePersonOperation:
    """
    Mutation operation for Person.
    GraphQL mutation: CreatePerson
    """
    
    query = CREATE_PERSON_MUTATION
    operation_type = "mutation"
    operation_name = "CreatePerson"
    
    
    class Variables(TypedDict):
        """Variable types for CreatePerson mutation."""
        
        input: CreatePersonInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, input: Union[CreatePersonInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            input: CreatePersonInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class DeleteApiKeyOperation:
    """
    Mutation operation for ApiKey.
    GraphQL mutation: DeleteApiKey
    """
    
    query = DELETE_API_KEY_MUTATION
    operation_type = "mutation"
    operation_name = "DeleteApiKey"
    
    
    class Variables(TypedDict):
        """Variable types for DeleteApiKey mutation."""
        
        id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(id, '__strawberry_definition__'):
            variables["id"] = strawberry.asdict(id)
        else:
            variables["id"] = id
        
        
        return variables


class DeleteDiagramOperation:
    """
    Mutation operation for Diagram.
    GraphQL mutation: DeleteDiagram
    """
    
    query = DELETE_DIAGRAM_MUTATION
    operation_type = "mutation"
    operation_name = "DeleteDiagram"
    
    
    class Variables(TypedDict):
        """Variable types for DeleteDiagram mutation."""
        
        id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(id, '__strawberry_definition__'):
            variables["id"] = strawberry.asdict(id)
        else:
            variables["id"] = id
        
        
        return variables


class DeleteNodeOperation:
    """
    Mutation operation for Node.
    GraphQL mutation: DeleteNode
    """
    
    query = DELETE_NODE_MUTATION
    operation_type = "mutation"
    operation_name = "DeleteNode"
    
    
    class Variables(TypedDict):
        """Variable types for DeleteNode mutation."""
        
        diagram_id: str
        
        node_id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, diagram_id: str, node_id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            diagram_id: ID - Required (accepts dict or Strawberry input object)
            
            node_id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(diagram_id, '__strawberry_definition__'):
            variables["diagram_id"] = strawberry.asdict(diagram_id)
        else:
            variables["diagram_id"] = diagram_id
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(node_id, '__strawberry_definition__'):
            variables["node_id"] = strawberry.asdict(node_id)
        else:
            variables["node_id"] = node_id
        
        
        return variables


class DeletePersonOperation:
    """
    Mutation operation for Person.
    GraphQL mutation: DeletePerson
    """
    
    query = DELETE_PERSON_MUTATION
    operation_type = "mutation"
    operation_name = "DeletePerson"
    
    
    class Variables(TypedDict):
        """Variable types for DeletePerson mutation."""
        
        id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(id, '__strawberry_definition__'):
            variables["id"] = strawberry.asdict(id)
        else:
            variables["id"] = id
        
        
        return variables


class ExecuteDiagramOperation:
    """
    Mutation operation for Diagram.
    GraphQL mutation: ExecuteDiagram
    """
    
    query = EXECUTE_DIAGRAM_MUTATION
    operation_type = "mutation"
    operation_name = "ExecuteDiagram"
    
    
    class Variables(TypedDict):
        """Variable types for ExecuteDiagram mutation."""
        
        input: ExecuteDiagramInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, input: Union[ExecuteDiagramInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            input: ExecuteDiagramInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class RegisterCliSessionOperation:
    """
    Mutation operation for CliSession.
    GraphQL mutation: RegisterCliSession
    """
    
    query = REGISTER_CLI_SESSION_MUTATION
    operation_type = "mutation"
    operation_name = "RegisterCliSession"
    
    
    class Variables(TypedDict):
        """Variable types for RegisterCliSession mutation."""
        
        input: RegisterCliSessionInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, input: Union[RegisterCliSessionInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            input: RegisterCliSessionInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class SendInteractiveResponseOperation:
    """
    Mutation operation for Execution.
    GraphQL mutation: SendInteractiveResponse
    """
    
    query = SEND_INTERACTIVE_RESPONSE_MUTATION
    operation_type = "mutation"
    operation_name = "SendInteractiveResponse"
    
    
    class Variables(TypedDict):
        """Variable types for SendInteractiveResponse mutation."""
        
        input: InteractiveResponseInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, input: Union[InteractiveResponseInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            input: InteractiveResponseInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class TestApiKeyOperation:
    """
    Mutation operation for ApiKey.
    GraphQL mutation: TestApiKey
    """
    
    query = TEST_API_KEY_MUTATION
    operation_type = "mutation"
    operation_name = "TestApiKey"
    
    
    class Variables(TypedDict):
        """Variable types for TestApiKey mutation."""
        
        id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(id, '__strawberry_definition__'):
            variables["id"] = strawberry.asdict(id)
        else:
            variables["id"] = id
        
        
        return variables


class UnregisterCliSessionOperation:
    """
    Mutation operation for CliSession.
    GraphQL mutation: UnregisterCliSession
    """
    
    query = UNREGISTER_CLI_SESSION_MUTATION
    operation_type = "mutation"
    operation_name = "UnregisterCliSession"
    
    
    class Variables(TypedDict):
        """Variable types for UnregisterCliSession mutation."""
        
        input: UnregisterCliSessionInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, input: Union[UnregisterCliSessionInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            input: UnregisterCliSessionInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class UpdateNodeOperation:
    """
    Mutation operation for Node.
    GraphQL mutation: UpdateNode
    """
    
    query = UPDATE_NODE_MUTATION
    operation_type = "mutation"
    operation_name = "UpdateNode"
    
    
    class Variables(TypedDict):
        """Variable types for UpdateNode mutation."""
        
        diagram_id: str
        
        node_id: str
        
        input: UpdateNodeInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, diagram_id: str, node_id: str, input: Union[UpdateNodeInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            diagram_id: ID - Required (accepts dict or Strawberry input object)
            
            node_id: ID - Required (accepts dict or Strawberry input object)
            
            input: UpdateNodeInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(diagram_id, '__strawberry_definition__'):
            variables["diagram_id"] = strawberry.asdict(diagram_id)
        else:
            variables["diagram_id"] = diagram_id
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(node_id, '__strawberry_definition__'):
            variables["node_id"] = strawberry.asdict(node_id)
        else:
            variables["node_id"] = node_id
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class UpdateNodeStateOperation:
    """
    Mutation operation for Execution.
    GraphQL mutation: UpdateNodeState
    """
    
    query = UPDATE_NODE_STATE_MUTATION
    operation_type = "mutation"
    operation_name = "UpdateNodeState"
    
    
    class Variables(TypedDict):
        """Variable types for UpdateNodeState mutation."""
        
        input: UpdateNodeStateInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, input: Union[UpdateNodeStateInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            input: UpdateNodeStateInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class UpdatePersonOperation:
    """
    Mutation operation for Person.
    GraphQL mutation: UpdatePerson
    """
    
    query = UPDATE_PERSON_MUTATION
    operation_type = "mutation"
    operation_name = "UpdatePerson"
    
    
    class Variables(TypedDict):
        """Variable types for UpdatePerson mutation."""
        
        id: str
        
        input: UpdatePersonInput
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, id: str, input: Union[UpdatePersonInput, dict[str, Any]]) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            id: ID - Required (accepts dict or Strawberry input object)
            
            input: UpdatePersonInput - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(id, '__strawberry_definition__'):
            variables["id"] = strawberry.asdict(id)
        else:
            variables["id"] = id
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(input, '__strawberry_definition__'):
            variables["input"] = strawberry.asdict(input)
        else:
            variables["input"] = input
        
        
        return variables


class UploadDiagramOperation:
    """
    Mutation operation for File.
    GraphQL mutation: UploadDiagram
    """
    
    query = UPLOAD_DIAGRAM_MUTATION
    operation_type = "mutation"
    operation_name = "UploadDiagram"
    
    
    class Variables(TypedDict):
        """Variable types for UploadDiagram mutation."""
        
        file: Any
        
        format: DiagramFormat
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, file: Any, format: DiagramFormat) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            file: Upload - Required (accepts dict or Strawberry input object)
            
            format: DiagramFormat - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(file, '__strawberry_definition__'):
            variables["file"] = strawberry.asdict(file)
        else:
            variables["file"] = file
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(format, '__strawberry_definition__'):
            variables["format"] = strawberry.asdict(format)
        else:
            variables["format"] = format
        
        
        return variables


class UploadFileOperation:
    """
    Mutation operation for File.
    GraphQL mutation: UploadFile
    """
    
    query = UPLOAD_FILE_MUTATION
    operation_type = "mutation"
    operation_name = "UploadFile"
    
    
    class Variables(TypedDict, total=False):
        """Variable types for UploadFile mutation."""
        
        file: Any
        
        path: Optional[str]
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, file: Any, path: Optional[str] = None) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            file: Upload - Required (accepts dict or Strawberry input object)
            
            path: String - Optional (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(file, '__strawberry_definition__'):
            variables["file"] = strawberry.asdict(file)
        else:
            variables["file"] = file
        
        
        
        if path is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(path, '__strawberry_definition__'):
                variables["path"] = strawberry.asdict(path)
            else:
                variables["path"] = path
        
        
        return variables


class ValidateDiagramOperation:
    """
    Mutation operation for File.
    GraphQL mutation: ValidateDiagram
    """
    
    query = VALIDATE_DIAGRAM_MUTATION
    operation_type = "mutation"
    operation_name = "ValidateDiagram"
    
    
    class Variables(TypedDict):
        """Variable types for ValidateDiagram mutation."""
        
        content: str
        
        format: DiagramFormat
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, content: str, format: DiagramFormat) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            content: String - Required (accepts dict or Strawberry input object)
            
            format: DiagramFormat - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(content, '__strawberry_definition__'):
            variables["content"] = strawberry.asdict(content)
        else:
            variables["content"] = content
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(format, '__strawberry_definition__'):
            variables["format"] = strawberry.asdict(format)
        else:
            variables["format"] = format
        
        
        return variables


class GetActiveCliSessionOperation:
    """
    Query operation for System.
    GraphQL query: GetActiveCliSession
    """
    
    query = GET_ACTIVE_CLI_SESSION_QUERY
    operation_type = "query"
    operation_name = "GetActiveCliSession"
    
    
    class Variables(TypedDict):
        """No variables for this operation."""
        pass
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, ) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        return variables


class GetApiKeyOperation:
    """
    Query operation for ApiKey.
    GraphQL query: GetApiKey
    """
    
    query = GET_API_KEY_QUERY
    operation_type = "query"
    operation_name = "GetApiKey"
    
    
    class Variables(TypedDict):
        """Variable types for GetApiKey query."""
        
        id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(id, '__strawberry_definition__'):
            variables["id"] = strawberry.asdict(id)
        else:
            variables["id"] = id
        
        
        return variables


class GetApiKeysOperation:
    """
    Query operation for ApiKey.
    GraphQL query: GetApiKeys
    """
    
    query = GET_API_KEYS_QUERY
    operation_type = "query"
    operation_name = "GetApiKeys"
    
    
    class Variables(TypedDict, total=False):
        """Variable types for GetApiKeys query."""
        
        service: Optional[str]
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, service: Optional[str] = None) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            service: String - Optional (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        if service is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(service, '__strawberry_definition__'):
                variables["service"] = strawberry.asdict(service)
            else:
                variables["service"] = service
        
        
        return variables


class GetAvailableModelsOperation:
    """
    Query operation for ApiKey.
    GraphQL query: GetAvailableModels
    """
    
    query = GET_AVAILABLE_MODELS_QUERY
    operation_type = "query"
    operation_name = "GetAvailableModels"
    
    
    class Variables(TypedDict):
        """Variable types for GetAvailableModels query."""
        
        service: str
        
        apiKeyId: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, service: str, apiKeyId: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            service: String - Required (accepts dict or Strawberry input object)
            
            apiKeyId: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(service, '__strawberry_definition__'):
            variables["service"] = strawberry.asdict(service)
        else:
            variables["service"] = service
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(apiKeyId, '__strawberry_definition__'):
            variables["apiKeyId"] = strawberry.asdict(apiKeyId)
        else:
            variables["apiKeyId"] = apiKeyId
        
        
        return variables


class GetDiagramOperation:
    """
    Query operation for Diagram.
    GraphQL query: GetDiagram
    """
    
    query = GET_DIAGRAM_QUERY
    operation_type = "query"
    operation_name = "GetDiagram"
    
    
    class Variables(TypedDict):
        """Variable types for GetDiagram query."""
        
        id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(id, '__strawberry_definition__'):
            variables["id"] = strawberry.asdict(id)
        else:
            variables["id"] = id
        
        
        return variables


class GetExecutionOperation:
    """
    Query operation for Execution.
    GraphQL query: GetExecution
    """
    
    query = GET_EXECUTION_QUERY
    operation_type = "query"
    operation_name = "GetExecution"
    
    
    class Variables(TypedDict):
        """Variable types for GetExecution query."""
        
        id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(id, '__strawberry_definition__'):
            variables["id"] = strawberry.asdict(id)
        else:
            variables["id"] = id
        
        
        return variables


class GetExecutionCapabilitiesOperation:
    """
    Query operation for System.
    GraphQL query: GetExecutionCapabilities
    """
    
    query = GET_EXECUTION_CAPABILITIES_QUERY
    operation_type = "query"
    operation_name = "GetExecutionCapabilities"
    
    
    class Variables(TypedDict):
        """No variables for this operation."""
        pass
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, ) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        return variables


class GetExecutionHistoryOperation:
    """
    Query operation for System.
    GraphQL query: GetExecutionHistory
    """
    
    query = GET_EXECUTION_HISTORY_QUERY
    operation_type = "query"
    operation_name = "GetExecutionHistory"
    
    
    class Variables(TypedDict, total=False):
        """Variable types for GetExecutionHistory query."""
        
        diagram_id: Optional[str]
        
        limit: Optional[int]
        
        include_metrics: Optional[bool]
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, diagram_id: Optional[str] = None, limit: Optional[int] = None, include_metrics: Optional[bool] = None) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            diagram_id: ID - Optional (accepts dict or Strawberry input object)
            
            limit: Int - Optional (accepts dict or Strawberry input object)
            
            include_metrics: Boolean - Optional (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        if diagram_id is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(diagram_id, '__strawberry_definition__'):
                variables["diagram_id"] = strawberry.asdict(diagram_id)
            else:
                variables["diagram_id"] = diagram_id
        
        
        
        if limit is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(limit, '__strawberry_definition__'):
                variables["limit"] = strawberry.asdict(limit)
            else:
                variables["limit"] = limit
        
        
        
        if include_metrics is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(include_metrics, '__strawberry_definition__'):
                variables["include_metrics"] = strawberry.asdict(include_metrics)
            else:
                variables["include_metrics"] = include_metrics
        
        
        return variables


class GetExecutionMetricsOperation:
    """
    Query operation for System.
    GraphQL query: GetExecutionMetrics
    """
    
    query = GET_EXECUTION_METRICS_QUERY
    operation_type = "query"
    operation_name = "GetExecutionMetrics"
    
    
    class Variables(TypedDict):
        """Variable types for GetExecutionMetrics query."""
        
        execution_id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, execution_id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            execution_id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(execution_id, '__strawberry_definition__'):
            variables["execution_id"] = strawberry.asdict(execution_id)
        else:
            variables["execution_id"] = execution_id
        
        
        return variables


class GetExecutionOrderOperation:
    """
    Query operation for System.
    GraphQL query: GetExecutionOrder
    """
    
    query = GET_EXECUTION_ORDER_QUERY
    operation_type = "query"
    operation_name = "GetExecutionOrder"
    
    
    class Variables(TypedDict):
        """Variable types for GetExecutionOrder query."""
        
        execution_id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, execution_id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            execution_id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(execution_id, '__strawberry_definition__'):
            variables["execution_id"] = strawberry.asdict(execution_id)
        else:
            variables["execution_id"] = execution_id
        
        
        return variables


class GetOperationSchemaOperation:
    """
    Query operation for Provider.
    GraphQL query: GetOperationSchema
    """
    
    query = GET_OPERATION_SCHEMA_QUERY
    operation_type = "query"
    operation_name = "GetOperationSchema"
    
    
    class Variables(TypedDict):
        """Variable types for GetOperationSchema query."""
        
        provider: str
        
        operation: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, provider: str, operation: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            provider: String - Required (accepts dict or Strawberry input object)
            
            operation: String - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(provider, '__strawberry_definition__'):
            variables["provider"] = strawberry.asdict(provider)
        else:
            variables["provider"] = provider
        
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(operation, '__strawberry_definition__'):
            variables["operation"] = strawberry.asdict(operation)
        else:
            variables["operation"] = operation
        
        
        return variables


class GetPersonOperation:
    """
    Query operation for Person.
    GraphQL query: GetPerson
    """
    
    query = GET_PERSON_QUERY
    operation_type = "query"
    operation_name = "GetPerson"
    
    
    class Variables(TypedDict):
        """Variable types for GetPerson query."""
        
        id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(id, '__strawberry_definition__'):
            variables["id"] = strawberry.asdict(id)
        else:
            variables["id"] = id
        
        
        return variables


class GetPromptFileOperation:
    """
    Query operation for Prompt.
    GraphQL query: GetPromptFile
    """
    
    query = GET_PROMPT_FILE_QUERY
    operation_type = "query"
    operation_name = "GetPromptFile"
    
    
    class Variables(TypedDict):
        """Variable types for GetPromptFile query."""
        
        filename: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, filename: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            filename: String - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(filename, '__strawberry_definition__'):
            variables["filename"] = strawberry.asdict(filename)
        else:
            variables["filename"] = filename
        
        
        return variables


class GetProviderOperationsOperation:
    """
    Query operation for Provider.
    GraphQL query: GetProviderOperations
    """
    
    query = GET_PROVIDER_OPERATIONS_QUERY
    operation_type = "query"
    operation_name = "GetProviderOperations"
    
    
    class Variables(TypedDict):
        """Variable types for GetProviderOperations query."""
        
        provider: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, provider: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            provider: String - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(provider, '__strawberry_definition__'):
            variables["provider"] = strawberry.asdict(provider)
        else:
            variables["provider"] = provider
        
        
        return variables


class GetProvidersOperation:
    """
    Query operation for Provider.
    GraphQL query: GetProviders
    """
    
    query = GET_PROVIDERS_QUERY
    operation_type = "query"
    operation_name = "GetProviders"
    
    
    class Variables(TypedDict):
        """No variables for this operation."""
        pass
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, ) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        return variables


class GetSupportedFormatsOperation:
    """
    Query operation for Format.
    GraphQL query: GetSupportedFormats
    """
    
    query = GET_SUPPORTED_FORMATS_QUERY
    operation_type = "query"
    operation_name = "GetSupportedFormats"
    
    
    class Variables(TypedDict):
        """No variables for this operation."""
        pass
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, ) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        return variables


class GetSystemInfoOperation:
    """
    Query operation for System.
    GraphQL query: GetSystemInfo
    """
    
    query = GET_SYSTEM_INFO_QUERY
    operation_type = "query"
    operation_name = "GetSystemInfo"
    
    
    class Variables(TypedDict):
        """No variables for this operation."""
        pass
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, ) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        return variables


class HealthCheckOperation:
    """
    Query operation for System.
    GraphQL query: HealthCheck
    """
    
    query = HEALTH_CHECK_QUERY
    operation_type = "query"
    operation_name = "HealthCheck"
    
    
    class Variables(TypedDict):
        """No variables for this operation."""
        pass
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, ) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        return variables


class ListConversationsOperation:
    """
    Query operation for Conversation.
    GraphQL query: ListConversations
    """
    
    query = LIST_CONVERSATIONS_QUERY
    operation_type = "query"
    operation_name = "ListConversations"
    
    
    class Variables(TypedDict, total=False):
        """Variable types for ListConversations query."""
        
        person_id: Optional[str]
        
        execution_id: Optional[str]
        
        search: Optional[str]
        
        show_forgotten: Optional[bool]
        
        limit: Optional[int]
        
        offset: Optional[int]
        
        since: Optional[str]
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, person_id: Optional[str] = None, execution_id: Optional[str] = None, search: Optional[str] = None, show_forgotten: Optional[bool] = None, limit: Optional[int] = None, offset: Optional[int] = None, since: Optional[str] = None) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            person_id: ID - Optional (accepts dict or Strawberry input object)
            
            execution_id: ID - Optional (accepts dict or Strawberry input object)
            
            search: String - Optional (accepts dict or Strawberry input object)
            
            show_forgotten: Boolean - Optional (accepts dict or Strawberry input object)
            
            limit: Int - Optional (accepts dict or Strawberry input object)
            
            offset: Int - Optional (accepts dict or Strawberry input object)
            
            since: DateTime - Optional (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        if person_id is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(person_id, '__strawberry_definition__'):
                variables["person_id"] = strawberry.asdict(person_id)
            else:
                variables["person_id"] = person_id
        
        
        
        if execution_id is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(execution_id, '__strawberry_definition__'):
                variables["execution_id"] = strawberry.asdict(execution_id)
            else:
                variables["execution_id"] = execution_id
        
        
        
        if search is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(search, '__strawberry_definition__'):
                variables["search"] = strawberry.asdict(search)
            else:
                variables["search"] = search
        
        
        
        if show_forgotten is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(show_forgotten, '__strawberry_definition__'):
                variables["show_forgotten"] = strawberry.asdict(show_forgotten)
            else:
                variables["show_forgotten"] = show_forgotten
        
        
        
        if limit is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(limit, '__strawberry_definition__'):
                variables["limit"] = strawberry.asdict(limit)
            else:
                variables["limit"] = limit
        
        
        
        if offset is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(offset, '__strawberry_definition__'):
                variables["offset"] = strawberry.asdict(offset)
            else:
                variables["offset"] = offset
        
        
        
        if since is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(since, '__strawberry_definition__'):
                variables["since"] = strawberry.asdict(since)
            else:
                variables["since"] = since
        
        
        return variables


class ListDiagramsOperation:
    """
    Query operation for Diagram.
    GraphQL query: ListDiagrams
    """
    
    query = LIST_DIAGRAMS_QUERY
    operation_type = "query"
    operation_name = "ListDiagrams"
    
    
    class Variables(TypedDict, total=False):
        """Variable types for ListDiagrams query."""
        
        filter: Optional[DiagramFilterInput]
        
        limit: Optional[int]
        
        offset: Optional[int]
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, filter: Optional[Union[DiagramFilterInput, dict[str, Any]]] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            filter: DiagramFilterInput - Optional (accepts dict or Strawberry input object)
            
            limit: Int - Optional (accepts dict or Strawberry input object)
            
            offset: Int - Optional (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        if filter is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(filter, '__strawberry_definition__'):
                variables["filter"] = strawberry.asdict(filter)
            else:
                variables["filter"] = filter
        
        
        
        if limit is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(limit, '__strawberry_definition__'):
                variables["limit"] = strawberry.asdict(limit)
            else:
                variables["limit"] = limit
        
        
        
        if offset is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(offset, '__strawberry_definition__'):
                variables["offset"] = strawberry.asdict(offset)
            else:
                variables["offset"] = offset
        
        
        return variables


class ListExecutionsOperation:
    """
    Query operation for Execution.
    GraphQL query: ListExecutions
    """
    
    query = LIST_EXECUTIONS_QUERY
    operation_type = "query"
    operation_name = "ListExecutions"
    
    
    class Variables(TypedDict, total=False):
        """Variable types for ListExecutions query."""
        
        filter: Optional[ExecutionFilterInput]
        
        limit: Optional[int]
        
        offset: Optional[int]
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, filter: Optional[Union[ExecutionFilterInput, dict[str, Any]]] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            filter: ExecutionFilterInput - Optional (accepts dict or Strawberry input object)
            
            limit: Int - Optional (accepts dict or Strawberry input object)
            
            offset: Int - Optional (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        if filter is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(filter, '__strawberry_definition__'):
                variables["filter"] = strawberry.asdict(filter)
            else:
                variables["filter"] = filter
        
        
        
        if limit is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(limit, '__strawberry_definition__'):
                variables["limit"] = strawberry.asdict(limit)
            else:
                variables["limit"] = limit
        
        
        
        if offset is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(offset, '__strawberry_definition__'):
                variables["offset"] = strawberry.asdict(offset)
            else:
                variables["offset"] = offset
        
        
        return variables


class ListPersonsOperation:
    """
    Query operation for Person.
    GraphQL query: ListPersons
    """
    
    query = LIST_PERSONS_QUERY
    operation_type = "query"
    operation_name = "ListPersons"
    
    
    class Variables(TypedDict, total=False):
        """Variable types for ListPersons query."""
        
        limit: Optional[int]
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, limit: Optional[int] = None) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            limit: Int - Optional (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        if limit is not None:
            # Convert Strawberry input object to dict if needed
            if hasattr(limit, '__strawberry_definition__'):
                variables["limit"] = strawberry.asdict(limit)
            else:
                variables["limit"] = limit
        
        
        return variables


class ListPromptFilesOperation:
    """
    Query operation for Prompt.
    GraphQL query: ListPromptFiles
    """
    
    query = LIST_PROMPT_FILES_QUERY
    operation_type = "query"
    operation_name = "ListPromptFiles"
    
    
    class Variables(TypedDict):
        """No variables for this operation."""
        pass
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, ) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        return variables


class ExecutionUpdatesOperation:
    """
    Subscription operation for Execution.
    GraphQL subscription: ExecutionUpdates
    """
    
    query = EXECUTION_UPDATES_SUBSCRIPTION
    operation_type = "subscription"
    operation_name = "ExecutionUpdates"
    
    
    class Variables(TypedDict):
        """Variable types for ExecutionUpdates subscription."""
        
        execution_id: str
        
    
    
    @classmethod
    def get_query(cls) -> str:
        """Get the GraphQL query string."""
        return cls.query
    
    @classmethod
    def get_variables_dict(cls, execution_id: str) -> dict[str, Any]:
        """
        Build variables dictionary for the operation.
        
        Args:
            
            execution_id: ID - Required (accepts dict or Strawberry input object)
            
        
        Returns:
            Dictionary of variables for GraphQL execution
        """
        variables = {}
        
        
        # Convert Strawberry input object to dict if needed
        if hasattr(execution_id, '__strawberry_definition__'):
            variables["execution_id"] = strawberry.asdict(execution_id)
        else:
            variables["execution_id"] = execution_id
        
        
        return variables


# Operation registries for runtime lookup
QUERIES = {
    
    "GetActiveCliSession": GetActiveCliSessionOperation,
    
    "GetApiKey": GetApiKeyOperation,
    
    "GetApiKeys": GetApiKeysOperation,
    
    "GetAvailableModels": GetAvailableModelsOperation,
    
    "GetDiagram": GetDiagramOperation,
    
    "GetExecution": GetExecutionOperation,
    
    "GetExecutionCapabilities": GetExecutionCapabilitiesOperation,
    
    "GetExecutionHistory": GetExecutionHistoryOperation,
    
    "GetExecutionMetrics": GetExecutionMetricsOperation,
    
    "GetExecutionOrder": GetExecutionOrderOperation,
    
    "GetOperationSchema": GetOperationSchemaOperation,
    
    "GetPerson": GetPersonOperation,
    
    "GetPromptFile": GetPromptFileOperation,
    
    "GetProviderOperations": GetProviderOperationsOperation,
    
    "GetProviders": GetProvidersOperation,
    
    "GetSupportedFormats": GetSupportedFormatsOperation,
    
    "GetSystemInfo": GetSystemInfoOperation,
    
    "HealthCheck": HealthCheckOperation,
    
    "ListConversations": ListConversationsOperation,
    
    "ListDiagrams": ListDiagramsOperation,
    
    "ListExecutions": ListExecutionsOperation,
    
    "ListPersons": ListPersonsOperation,
    
    "ListPromptFiles": ListPromptFilesOperation,
    
}

MUTATIONS = {
    
    "ControlExecution": ControlExecutionOperation,
    
    "ConvertDiagramFormat": ConvertDiagramFormatOperation,
    
    "CreateApiKey": CreateApiKeyOperation,
    
    "CreateDiagram": CreateDiagramOperation,
    
    "CreateNode": CreateNodeOperation,
    
    "CreatePerson": CreatePersonOperation,
    
    "DeleteApiKey": DeleteApiKeyOperation,
    
    "DeleteDiagram": DeleteDiagramOperation,
    
    "DeleteNode": DeleteNodeOperation,
    
    "DeletePerson": DeletePersonOperation,
    
    "ExecuteDiagram": ExecuteDiagramOperation,
    
    "RegisterCliSession": RegisterCliSessionOperation,
    
    "SendInteractiveResponse": SendInteractiveResponseOperation,
    
    "TestApiKey": TestApiKeyOperation,
    
    "UnregisterCliSession": UnregisterCliSessionOperation,
    
    "UpdateNode": UpdateNodeOperation,
    
    "UpdateNodeState": UpdateNodeStateOperation,
    
    "UpdatePerson": UpdatePersonOperation,
    
    "UploadDiagram": UploadDiagramOperation,
    
    "UploadFile": UploadFileOperation,
    
    "ValidateDiagram": ValidateDiagramOperation,
    
}

SUBSCRIPTIONS = {
    
    "ExecutionUpdates": ExecutionUpdatesOperation,
    
}

ALL_OPERATIONS = {
    **QUERIES,
    **MUTATIONS,
    **SUBSCRIPTIONS,
}

# Helper functions
def get_operation_by_name(name: str) -> Optional[type]:
    """Get an operation class by its name."""
    return ALL_OPERATIONS.get(name)

def get_query_string(operation_name: str) -> Optional[str]:
    """Get the GraphQL query string for an operation."""
    operation_class = get_operation_by_name(operation_name)
    if operation_class:
        return operation_class.get_query()
    return None

# Export all operation classes
__all__ = [
    # Query strings
    
    "CONTROL_EXECUTION_MUTATION",
    
    "CONVERT_DIAGRAM_FORMAT_MUTATION",
    
    "CREATE_API_KEY_MUTATION",
    
    "CREATE_DIAGRAM_MUTATION",
    
    "CREATE_NODE_MUTATION",
    
    "CREATE_PERSON_MUTATION",
    
    "DELETE_API_KEY_MUTATION",
    
    "DELETE_DIAGRAM_MUTATION",
    
    "DELETE_NODE_MUTATION",
    
    "DELETE_PERSON_MUTATION",
    
    "EXECUTE_DIAGRAM_MUTATION",
    
    "REGISTER_CLI_SESSION_MUTATION",
    
    "SEND_INTERACTIVE_RESPONSE_MUTATION",
    
    "TEST_API_KEY_MUTATION",
    
    "UNREGISTER_CLI_SESSION_MUTATION",
    
    "UPDATE_NODE_MUTATION",
    
    "UPDATE_NODE_STATE_MUTATION",
    
    "UPDATE_PERSON_MUTATION",
    
    "UPLOAD_DIAGRAM_MUTATION",
    
    "UPLOAD_FILE_MUTATION",
    
    "VALIDATE_DIAGRAM_MUTATION",
    
    "GET_ACTIVE_CLI_SESSION_QUERY",
    
    "GET_API_KEY_QUERY",
    
    "GET_API_KEYS_QUERY",
    
    "GET_AVAILABLE_MODELS_QUERY",
    
    "GET_DIAGRAM_QUERY",
    
    "GET_EXECUTION_QUERY",
    
    "GET_EXECUTION_CAPABILITIES_QUERY",
    
    "GET_EXECUTION_HISTORY_QUERY",
    
    "GET_EXECUTION_METRICS_QUERY",
    
    "GET_EXECUTION_ORDER_QUERY",
    
    "GET_OPERATION_SCHEMA_QUERY",
    
    "GET_PERSON_QUERY",
    
    "GET_PROMPT_FILE_QUERY",
    
    "GET_PROVIDER_OPERATIONS_QUERY",
    
    "GET_PROVIDERS_QUERY",
    
    "GET_SUPPORTED_FORMATS_QUERY",
    
    "GET_SYSTEM_INFO_QUERY",
    
    "HEALTH_CHECK_QUERY",
    
    "LIST_CONVERSATIONS_QUERY",
    
    "LIST_DIAGRAMS_QUERY",
    
    "LIST_EXECUTIONS_QUERY",
    
    "LIST_PERSONS_QUERY",
    
    "LIST_PROMPT_FILES_QUERY",
    
    "EXECUTION_UPDATES_SUBSCRIPTION",
    
    # Operation classes
    
    "ControlExecutionOperation",
    
    "ConvertDiagramFormatOperation",
    
    "CreateApiKeyOperation",
    
    "CreateDiagramOperation",
    
    "CreateNodeOperation",
    
    "CreatePersonOperation",
    
    "DeleteApiKeyOperation",
    
    "DeleteDiagramOperation",
    
    "DeleteNodeOperation",
    
    "DeletePersonOperation",
    
    "ExecuteDiagramOperation",
    
    "RegisterCliSessionOperation",
    
    "SendInteractiveResponseOperation",
    
    "TestApiKeyOperation",
    
    "UnregisterCliSessionOperation",
    
    "UpdateNodeOperation",
    
    "UpdateNodeStateOperation",
    
    "UpdatePersonOperation",
    
    "UploadDiagramOperation",
    
    "UploadFileOperation",
    
    "ValidateDiagramOperation",
    
    "GetActiveCliSessionOperation",
    
    "GetApiKeyOperation",
    
    "GetApiKeysOperation",
    
    "GetAvailableModelsOperation",
    
    "GetDiagramOperation",
    
    "GetExecutionOperation",
    
    "GetExecutionCapabilitiesOperation",
    
    "GetExecutionHistoryOperation",
    
    "GetExecutionMetricsOperation",
    
    "GetExecutionOrderOperation",
    
    "GetOperationSchemaOperation",
    
    "GetPersonOperation",
    
    "GetPromptFileOperation",
    
    "GetProviderOperationsOperation",
    
    "GetProvidersOperation",
    
    "GetSupportedFormatsOperation",
    
    "GetSystemInfoOperation",
    
    "HealthCheckOperation",
    
    "ListConversationsOperation",
    
    "ListDiagramsOperation",
    
    "ListExecutionsOperation",
    
    "ListPersonsOperation",
    
    "ListPromptFilesOperation",
    
    "ExecutionUpdatesOperation",
    
    # Registries
    "QUERIES",
    "MUTATIONS", 
    "SUBSCRIPTIONS",
    "ALL_OPERATIONS",
    # Helper functions
    "get_operation_by_name",
    "get_query_string",
]