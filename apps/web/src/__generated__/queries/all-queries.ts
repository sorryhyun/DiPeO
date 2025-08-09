





import { gql } from '@apollo/client';
import type {
  CreateApiKeyInput,
  CreateDiagramInput,
  CreateNodeInput,
  CreatePersonInput,
  DiagramFilterInput,
  DiagramFormat,
  ExecuteDiagramInput,
  ExecutionControlInput,
  ExecutionFilterInput,
  InteractiveResponseInput,
  Scalars,
  UpdateNodeInput,
  UpdateNodeStateInput,
  UpdatePersonInput
} from '@dipeo/models';

type Upload = Scalars['Upload']['input'];export const CONTROLEXECUTION_MUTATION = gql`
  mutation ControlExecution(
    $input: ExecutionControlInput!
  ) {
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
  }
`;
export interface ControlExecutionVariables {
  input: ExecutionControlInput;
}export const CONVERTDIAGRAMFORMAT_MUTATION = gql`
  mutation ConvertDiagramFormat(
    $content: String!, 
    $from_format: DiagramFormat!, 
    $to_format: DiagramFormat!
  ) {
    convert_diagram_format(content: $content, from_format: $from_format, to_format: $to_format) {
      success
      content
      format
      message
      error
    }
  }
`;
export interface ConvertDiagramFormatVariables {
  content: string;
  from_format: DiagramFormat;
  to_format: DiagramFormat;
}export const CREATEAPIKEY_MUTATION = gql`
  mutation CreateApiKey(
    $input: CreateApiKeyInput!
  ) {
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
  }
`;
export interface CreateApiKeyVariables {
  input: CreateApiKeyInput;
}export const CREATEDIAGRAM_MUTATION = gql`
  mutation CreateDiagram(
    $input: CreateDiagramInput!
  ) {
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
  }
`;
export interface CreateDiagramVariables {
  input: CreateDiagramInput;
}export const CREATENODE_MUTATION = gql`
  mutation CreateNode(
    $diagram_id: ID!, 
    $input: CreateNodeInput!
  ) {
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
  }
`;
export interface CreateNodeVariables {
  diagram_id: string;
  input: CreateNodeInput;
}export const CREATEPERSON_MUTATION = gql`
  mutation CreatePerson(
    $input: CreatePersonInput!
  ) {
    create_person(input: $input) {
      success
      person {
        id
        label
      }
      message
      error
    }
  }
`;
export interface CreatePersonVariables {
  input: CreatePersonInput;
}export const DELETEAPIKEY_MUTATION = gql`
  mutation DeleteApiKey(
    $id: ID!
  ) {
    delete_api_key(id: $id) {
      success
      message
    }
  }
`;
export interface DeleteApiKeyVariables {
  id: string;
}export const DELETEDIAGRAM_MUTATION = gql`
  mutation DeleteDiagram(
    $id: ID!
  ) {
    delete_diagram(id: $id) {
      success
      message
      error
    }
  }
`;
export interface DeleteDiagramVariables {
  id: string;
}export const DELETENODE_MUTATION = gql`
  mutation DeleteNode(
    $diagram_id: ID!, 
    $node_id: ID!
  ) {
    delete_node(diagram_id: $diagram_id, node_id: $node_id) {
      success
      message
      error
    }
  }
`;
export interface DeleteNodeVariables {
  diagram_id: string;
  node_id: string;
}export const DELETEPERSON_MUTATION = gql`
  mutation DeletePerson(
    $id: ID!
  ) {
    delete_person(id: $id) {
      success
      message
      error
    }
  }
`;
export interface DeletePersonVariables {
  id: string;
}export const EXECUTEDIAGRAM_MUTATION = gql`
  mutation ExecuteDiagram(
    $input: ExecuteDiagramInput!
  ) {
    execute_diagram(input: $input) {
      success
      execution {
        id
      }
      message
      error
    }
  }
`;
export interface ExecuteDiagramVariables {
  input: ExecuteDiagramInput;
}export const REGISTERCLISESSION_MUTATION = gql`
  mutation RegisterCliSession(
    $input: RegisterCliSessionInput!
  ) {
    register_cli_session(input: $input) {
      success
      session_id
      message
      error
    }
  }
`;
export interface RegisterCliSessionVariables {
  input: RegisterCliSessionInput;
}export const SENDINTERACTIVERESPONSE_MUTATION = gql`
  mutation SendInteractiveResponse(
    $input: InteractiveResponseInput!
  ) {
    send_interactive_response(input: $input) {
      success
      execution_id
      message
      error
    }
  }
`;
export interface SendInteractiveResponseVariables {
  input: InteractiveResponseInput;
}export const TESTAPIKEY_MUTATION = gql`
  mutation TestApiKey(
    $id: ID!
  ) {
    test_api_key(id: $id) {
      success
      message
      error
    }
  }
`;
export interface TestApiKeyVariables {
  id: string;
}export const UNREGISTERCLISESSION_MUTATION = gql`
  mutation UnregisterCliSession(
    $input: UnregisterCliSessionInput!
  ) {
    unregister_cli_session(input: $input) {
      success
      message
      error
    }
  }
`;
export interface UnregisterCliSessionVariables {
  input: UnregisterCliSessionInput;
}export const UPDATENODE_MUTATION = gql`
  mutation UpdateNode(
    $diagram_id: ID!, 
    $node_id: ID!, 
    $input: UpdateNodeInput!
  ) {
    update_node(diagram_id: $diagram_id, node_id: $node_id, input: $input) {
      success
      message
      error
    }
  }
`;
export interface UpdateNodeVariables {
  diagram_id: string;
  node_id: string;
  input: UpdateNodeInput;
}export const UPDATENODESTATE_MUTATION = gql`
  mutation UpdateNodeState(
    $input: UpdateNodeStateInput!
  ) {
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
  }
`;
export interface UpdateNodeStateVariables {
  input: UpdateNodeStateInput;
}export const UPDATEPERSON_MUTATION = gql`
  mutation UpdatePerson(
    $id: ID!, 
    $input: UpdatePersonInput!
  ) {
    update_person(id: $id, input: $input) {
      success
      person {
        id
        label
      }
      message
      error
    }
  }
`;
export interface UpdatePersonVariables {
  id: string;
  input: UpdatePersonInput;
}export const UPLOADDIAGRAM_MUTATION = gql`
  mutation UploadDiagram(
    $file: Upload!, 
    $format: DiagramFormat!
  ) {
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
  }
`;
export interface UploadDiagramVariables {
  file: Upload;
  format: DiagramFormat;
}export const UPLOADFILE_MUTATION = gql`
  mutation UploadFile(
    $file: Upload!, 
    $path: String
  ) {
    upload_file(file: $file, path: $path) {
      success
      path
      size_bytes
      content_type
      message
      error
    }
  }
`;
export interface UploadFileVariables {
  file: Upload;
  path?: string;
}export const VALIDATEDIAGRAM_MUTATION = gql`
  mutation ValidateDiagram(
    $content: String!, 
    $format: DiagramFormat!
  ) {
    validate_diagram(content: $content, format: $format) {
      success
      errors
      warnings
      message
    }
  }
`;
export interface ValidateDiagramVariables {
  content: string;
  format: DiagramFormat;
}export const GETACTIVECLISESSION_QUERY = gql`
  query GetActiveCliSession {
    active_cli_session {
      execution_id
      diagram_name
      diagram_format
      started_at
      is_active
      diagram_data
    }
  }
`;export const GETAPIKEY_QUERY = gql`
  query GetApiKey(
    $id: ID!
  ) {
    api_key(id: $id) {
      id
      label
      service
    }
  }
`;
export interface GetApiKeyVariables {
  id: string;
}export const GETAPIKEYS_QUERY = gql`
  query GetApiKeys(
    $service: String
  ) {
    api_keys(service: $service) {
      id
      label
      service
      key
    }
  }
`;
export interface GetApiKeysVariables {
  service?: string;
}export const GETAVAILABLEMODELS_QUERY = gql`
  query GetAvailableModels(
    $service: String!, 
    $apiKeyId: ID!
  ) {
    available_models(service: $service, api_key_id: $apiKeyId)
  }
`;
export interface GetAvailableModelsVariables {
  service: string;
  apiKeyId: string;
}export const GETDIAGRAM_QUERY = gql`
  query GetDiagram(
    $id: ID!
  ) {
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
  }
`;
export interface GetDiagramVariables {
  id: string;
}export const GETEXECUTION_QUERY = gql`
  query GetExecution(
    $id: ID!
  ) {
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
  }
`;
export interface GetExecutionVariables {
  id: string;
}export const GETEXECUTIONCAPABILITIES_QUERY = gql`
  query GetExecutionCapabilities {
    execution_capabilities
  }
`;export const GETEXECUTIONHISTORY_QUERY = gql`
  query GetExecutionHistory(
    $diagram_id: ID, 
    $limit: Int, 
    $include_metrics: Boolean
  ) {
    execution_history {
      id
      status
      diagram_id
      started_at
      ended_at
      error
      metrics
    }
  }
`;
export interface GetExecutionHistoryVariables {
  diagram_id?: string;
  limit?: number;
  include_metrics?: boolean;
}export const GETEXECUTIONMETRICS_QUERY = gql`
  query GetExecutionMetrics(
    $execution_id: ID!
  ) {
    execution_metrics(execution_id: $execution_id)
  }
`;
export interface GetExecutionMetricsVariables {
  execution_id: string;
}export const GETEXECUTIONORDER_QUERY = gql`
  query GetExecutionOrder(
    $execution_id: ID!
  ) {
    execution_order(execution_id: $execution_id)
  }
`;
export interface GetExecutionOrderVariables {
  execution_id: string;
}export const GETPERSON_QUERY = gql`
  query GetPerson(
    $id: ID!
  ) {
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
  }
`;
export interface GetPersonVariables {
  id: string;
}export const GETPROMPTFILE_QUERY = gql`
  query GetPromptFile(
    $filename: String!
  ) {
    prompt_file(filename: $filename)
  }
`;
export interface GetPromptFileVariables {
  filename: string;
}export const GETSUPPORTEDFORMATS_QUERY = gql`
  query GetSupportedFormats {
    supported_formats {
      format
      name
      description
      extension
      supports_import
      supports_export
    }
  }
`;export const GETSYSTEMINFO_QUERY = gql`
  query GetSystemInfo {
    system_info
  }
`;export const HEALTHCHECK_QUERY = gql`
  query HealthCheck {
    health
  }
`;export const LISTCONVERSATIONS_QUERY = gql`
  query ListConversations(
    $person_id: ID, 
    $execution_id: ID, 
    $search: String, 
    $show_forgotten: Boolean, 
    $limit: Int, 
    $offset: Int, 
    $since: DateTime
  ) {
    conversations(person_id: $person_id, execution_id: $execution_id, search: $search, show_forgotten: $show_forgotten, limit: $limit, offset: $offset, since: $since)
  }
`;
export interface ListConversationsVariables {
  person_id?: string;
  execution_id?: string;
  search?: string;
  show_forgotten?: boolean;
  limit?: number;
  offset?: number;
  since?: string;
}export const LISTDIAGRAMS_QUERY = gql`
  query ListDiagrams(
    $filter: DiagramFilterInput, 
    $limit: Int, 
    $offset: Int
  ) {
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
  }
`;
export interface ListDiagramsVariables {
  filter?: DiagramFilterInput;
  limit?: number;
  offset?: number;
}export const LISTEXECUTIONS_QUERY = gql`
  query ListExecutions(
    $filter: ExecutionFilterInput, 
    $limit: Int, 
    $offset: Int
  ) {
    executions(filter: $filter, limit: $limit, offset: $offset) {
      id
      status
      diagram_id
      started_at
      ended_at
      error
    }
  }
`;
export interface ListExecutionsVariables {
  filter?: ExecutionFilterInput;
  limit?: number;
  offset?: number;
}export const LISTPERSONS_QUERY = gql`
  query ListPersons(
    $limit: Int
  ) {
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
  }
`;
export interface ListPersonsVariables {
  limit?: number;
}export const LISTPROMPTFILES_QUERY = gql`
  query ListPromptFiles {
    prompt_files
  }
`;export const EXECUTIONUPDATES_SUBSCRIPTION = gql`
  subscription ExecutionUpdates(
    $execution_id: ID!
  ) {
    execution_updates(execution_id: $execution_id) {
      execution_id
      event_type
      data
      timestamp
    }
  }
`;
export interface ExecutionUpdatesVariables {
  execution_id: string;
}export const QUERIES = {
  GETACTIVECLISESSION: GETACTIVECLISESSION_QUERY,
  GETAPIKEY: GETAPIKEY_QUERY,
  GETAPIKEYS: GETAPIKEYS_QUERY,
  GETAVAILABLEMODELS: GETAVAILABLEMODELS_QUERY,
  GETDIAGRAM: GETDIAGRAM_QUERY,
  GETEXECUTION: GETEXECUTION_QUERY,
  GETEXECUTIONCAPABILITIES: GETEXECUTIONCAPABILITIES_QUERY,
  GETEXECUTIONHISTORY: GETEXECUTIONHISTORY_QUERY,
  GETEXECUTIONMETRICS: GETEXECUTIONMETRICS_QUERY,
  GETEXECUTIONORDER: GETEXECUTIONORDER_QUERY,
  GETPERSON: GETPERSON_QUERY,
  GETPROMPTFILE: GETPROMPTFILE_QUERY,
  GETSUPPORTEDFORMATS: GETSUPPORTEDFORMATS_QUERY,
  GETSYSTEMINFO: GETSYSTEMINFO_QUERY,
  HEALTHCHECK: HEALTHCHECK_QUERY,
  LISTCONVERSATIONS: LISTCONVERSATIONS_QUERY,
  LISTDIAGRAMS: LISTDIAGRAMS_QUERY,
  LISTEXECUTIONS: LISTEXECUTIONS_QUERY,
  LISTPERSONS: LISTPERSONS_QUERY,
  LISTPROMPTFILES: LISTPROMPTFILES_QUERY
} as const;

export const MUTATIONS = {
  CONTROLEXECUTION: CONTROLEXECUTION_MUTATION,
  CONVERTDIAGRAMFORMAT: CONVERTDIAGRAMFORMAT_MUTATION,
  CREATEAPIKEY: CREATEAPIKEY_MUTATION,
  CREATEDIAGRAM: CREATEDIAGRAM_MUTATION,
  CREATENODE: CREATENODE_MUTATION,
  CREATEPERSON: CREATEPERSON_MUTATION,
  DELETEAPIKEY: DELETEAPIKEY_MUTATION,
  DELETEDIAGRAM: DELETEDIAGRAM_MUTATION,
  DELETENODE: DELETENODE_MUTATION,
  DELETEPERSON: DELETEPERSON_MUTATION,
  EXECUTEDIAGRAM: EXECUTEDIAGRAM_MUTATION,
  REGISTERCLISESSION: REGISTERCLISESSION_MUTATION,
  SENDINTERACTIVERESPONSE: SENDINTERACTIVERESPONSE_MUTATION,
  TESTAPIKEY: TESTAPIKEY_MUTATION,
  UNREGISTERCLISESSION: UNREGISTERCLISESSION_MUTATION,
  UPDATENODE: UPDATENODE_MUTATION,
  UPDATENODESTATE: UPDATENODESTATE_MUTATION,
  UPDATEPERSON: UPDATEPERSON_MUTATION,
  UPLOADDIAGRAM: UPLOADDIAGRAM_MUTATION,
  UPLOADFILE: UPLOADFILE_MUTATION,
  VALIDATEDIAGRAM: VALIDATEDIAGRAM_MUTATION
} as const;

export const SUBSCRIPTIONS = {
  EXECUTIONUPDATES: EXECUTIONUPDATES_SUBSCRIPTION
} as const;export type QueryName = keyof typeof QUERIES;
export type MutationName = keyof typeof MUTATIONS;
export type SubscriptionName = keyof typeof SUBSCRIPTIONS;export const OPERATION_METADATA = {
  ControlExecution: {
    type: 'mutation',
    entity: 'Execution',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ConvertDiagramFormat: {
    type: 'mutation',
    entity: 'File',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CreateApiKey: {
    type: 'mutation',
    entity: 'ApiKey',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CreateDiagram: {
    type: 'mutation',
    entity: 'Diagram',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CreateNode: {
    type: 'mutation',
    entity: 'Node',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CreatePerson: {
    type: 'mutation',
    entity: 'Person',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  DeleteApiKey: {
    type: 'mutation',
    entity: 'ApiKey',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  DeleteDiagram: {
    type: 'mutation',
    entity: 'Diagram',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  DeleteNode: {
    type: 'mutation',
    entity: 'Node',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  DeletePerson: {
    type: 'mutation',
    entity: 'Person',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ExecuteDiagram: {
    type: 'mutation',
    entity: 'Diagram',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  RegisterCliSession: {
    type: 'mutation',
    entity: 'CliSession',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  SendInteractiveResponse: {
    type: 'mutation',
    entity: 'Execution',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  TestApiKey: {
    type: 'mutation',
    entity: 'ApiKey',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  UnregisterCliSession: {
    type: 'mutation',
    entity: 'CliSession',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  UpdateNode: {
    type: 'mutation',
    entity: 'Node',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  UpdateNodeState: {
    type: 'mutation',
    entity: 'Execution',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  UpdatePerson: {
    type: 'mutation',
    entity: 'Person',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  UploadDiagram: {
    type: 'mutation',
    entity: 'File',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  UploadFile: {
    type: 'mutation',
    entity: 'File',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ValidateDiagram: {
    type: 'mutation',
    entity: 'File',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetActiveCliSession: {
    type: 'query',
    entity: 'System',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetApiKey: {
    type: 'query',
    entity: 'ApiKey',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetApiKeys: {
    type: 'query',
    entity: 'ApiKey',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetAvailableModels: {
    type: 'query',
    entity: 'ApiKey',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetDiagram: {
    type: 'query',
    entity: 'Diagram',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetExecution: {
    type: 'query',
    entity: 'Execution',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetExecutionCapabilities: {
    type: 'query',
    entity: 'System',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetExecutionHistory: {
    type: 'query',
    entity: 'System',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetExecutionMetrics: {
    type: 'query',
    entity: 'System',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetExecutionOrder: {
    type: 'query',
    entity: 'System',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetPerson: {
    type: 'query',
    entity: 'Person',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetPromptFile: {
    type: 'query',
    entity: 'Prompt',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetSupportedFormats: {
    type: 'query',
    entity: 'Format',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetSystemInfo: {
    type: 'query',
    entity: 'System',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  HealthCheck: {
    type: 'query',
    entity: 'System',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ListConversations: {
    type: 'query',
    entity: 'Conversation',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ListDiagrams: {
    type: 'query',
    entity: 'Diagram',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ListExecutions: {
    type: 'query',
    entity: 'Execution',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ListPersons: {
    type: 'query',
    entity: 'Person',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ListPromptFiles: {
    type: 'query',
    entity: 'Prompt',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ExecutionUpdates: {
    type: 'subscription',
    entity: 'Execution',
    operation: '',
    fieldPreset: 'STANDARD',
  },
} as const;