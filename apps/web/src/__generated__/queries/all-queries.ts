





import { gql } from '@apollo/client';export const ADDMESSAGE_MUTATION = gql`
  mutation AddMessage(
    $conversationId: ID!, 
    $input: AddMessageInput!
  ) {
    add_message {
      success
      message {
        id
        role
        content
        timestamp
      }
      error
    }
  }
`;
export interface AddMessageVariables {
  conversationId: string;
  input: AddMessageInput;
}export const CANCELEXECUTION_MUTATION = gql`
  mutation CancelExecution(
    $id: ID!
  ) {
    cancel_execution {
      success
      message
      error
    }
  }
`;
export interface CancelExecutionVariables {
  id: string;
}export const CONVERTFORMAT_MUTATION = gql`
  mutation ConvertFormat(
    $input: ConvertFormatInput!
  ) {
    convert_format {
      success
      output
      format
      message
      error
    }
  }
`;
export interface ConvertFormatVariables {
  input: ConvertFormatInput;
}export const CREATEAPIKEY_MUTATION = gql`
  mutation CreateApiKey(
    $input: CreateApiKeyInput!
  ) {
    create_api_key {
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
}export const CREATECONVERSATION_MUTATION = gql`
  mutation CreateConversation(
    $input: CreateConversationInput!
  ) {
    create_conversation {
      success
      conversation {
        id
        title
      }
      message
      error
    }
  }
`;
export interface CreateConversationVariables {
  input: CreateConversationInput;
}export const CREATEDIAGRAM_MUTATION = gql`
  mutation CreateDiagram(
    $input: CreateDiagramInput!
  ) {
    create_diagram {
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
}export const CREATEFILE_MUTATION = gql`
  mutation CreateFile(
    $path: String!, 
    $content: String!
  ) {
    create_file {
      success
      file {
        path
        size
      }
      message
      error
    }
  }
`;
export interface CreateFileVariables {
  path: string;
  content: string;
}export const CREATEPERSON_MUTATION = gql`
  mutation CreatePerson(
    $input: CreatePersonInput!
  ) {
    create_person {
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
}export const CREATEPROMPTTEMPLATE_MUTATION = gql`
  mutation CreatePromptTemplate(
    $input: CreatePromptTemplateInput!
  ) {
    create_prompt_template {
      success
      template {
        id
        name
      }
      message
      error
    }
  }
`;
export interface CreatePromptTemplateVariables {
  input: CreatePromptTemplateInput;
}export const DELETEAPIKEY_MUTATION = gql`
  mutation DeleteApiKey(
    $id: ID!
  ) {
    delete_api_key {
      success
      message
    }
  }
`;
export interface DeleteApiKeyVariables {
  id: string;
}export const DELETECONVERSATION_MUTATION = gql`
  mutation DeleteConversation(
    $id: ID!
  ) {
    delete_conversation {
      success
      message
      error
    }
  }
`;
export interface DeleteConversationVariables {
  id: string;
}export const DELETEDIAGRAM_MUTATION = gql`
  mutation DeleteDiagram(
    $id: ID!
  ) {
    delete_diagram {
      success
      message
      error
    }
  }
`;
export interface DeleteDiagramVariables {
  id: string;
}export const DELETEFILE_MUTATION = gql`
  mutation DeleteFile(
    $path: String!
  ) {
    delete_file {
      success
      message
      error
    }
  }
`;
export interface DeleteFileVariables {
  path: string;
}export const DELETEPERSON_MUTATION = gql`
  mutation DeletePerson(
    $id: ID!
  ) {
    delete_person {
      success
      message
      error
    }
  }
`;
export interface DeletePersonVariables {
  id: string;
}export const DELETEPROMPTTEMPLATE_MUTATION = gql`
  mutation DeletePromptTemplate(
    $id: ID!
  ) {
    delete_prompt_template {
      success
      message
      error
    }
  }
`;
export interface DeletePromptTemplateVariables {
  id: string;
}export const EXECUTEDIAGRAM_MUTATION = gql`
  mutation ExecuteDiagram(
    $input: ExecuteDiagramInput!
  ) {
    execute_diagram {
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
}export const RENDERPROMPT_MUTATION = gql`
  mutation RenderPrompt(
    $templateId: ID!, 
    $variables: JSON!
  ) {
    render_prompt {
      success
      rendered
      error
    }
  }
`;
export interface RenderPromptVariables {
  templateId: string;
  variables: any;
}export const TESTAPIKEY_MUTATION = gql`
  mutation TestApiKey(
    $id: ID!
  ) {
    test_api_key {
      success
      message
      error
    }
  }
`;
export interface TestApiKeyVariables {
  id: string;
}export const UPDATEFILE_MUTATION = gql`
  mutation UpdateFile(
    $path: String!, 
    $content: String!
  ) {
    update_file {
      success
      file {
        path
        size
        modified
      }
      message
      error
    }
  }
`;
export interface UpdateFileVariables {
  path: string;
  content: string;
}export const UPDATEPERSON_MUTATION = gql`
  mutation UpdatePerson(
    $id: ID!, 
    $input: UpdatePersonInput!
  ) {
    update_person {
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
}export const UPDATEPROMPTTEMPLATE_MUTATION = gql`
  mutation UpdatePromptTemplate(
    $id: ID!, 
    $input: UpdatePromptTemplateInput!
  ) {
    update_prompt_template {
      success
      template {
        id
        name
      }
      message
      error
    }
  }
`;
export interface UpdatePromptTemplateVariables {
  id: string;
  input: UpdatePromptTemplateInput;
}export const VALIDATEFORMAT_MUTATION = gql`
  mutation ValidateFormat(
    $input: ValidateFormatInput!
  ) {
    validate_format {
      valid
      errors
      warnings
    }
  }
`;
export interface ValidateFormatVariables {
  input: ValidateFormatInput;
}export const VALIDATENODE_MUTATION = gql`
  mutation ValidateNode(
    $input: ValidateNodeInput!
  ) {
    validate_node {
      valid
      errors
      warnings
    }
  }
`;
export interface ValidateNodeVariables {
  input: ValidateNodeInput;
}export const GETAPIKEY_QUERY = gql`
  query GetApiKey(
    $id: ID!
  ) {
    api_key {
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
    api_keys {
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
    available_models
  }
`;
export interface GetAvailableModelsVariables {
  service: string;
  apiKeyId: string;
}export const GETCONVERSATION_QUERY = gql`
  query GetConversation(
    $id: ID!
  ) {
    conversation {
      id
      title
      created
      updated
      messages {
        id
        role
        content
        timestamp
      }
    }
  }
`;
export interface GetConversationVariables {
  id: string;
}export const GETDIAGRAM_QUERY = gql`
  query GetDiagram(
    $id: ID!
  ) {
    diagram {
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
    execution {
      id
      status
      phase
      diagram_id
      start_time
      end_time
      error
      node_states {
        node_id
        status
        start_time
        end_time
        error
        outputs
      }
    }
  }
`;
export interface GetExecutionVariables {
  id: string;
}export const GETFILE_QUERY = gql`
  query GetFile(
    $path: String!
  ) {
    file {
      name
      path
      content
      size
      modified
    }
  }
`;
export interface GetFileVariables {
  path: string;
}export const GETLLMMODELS_QUERY = gql`
  query GetLLMModels(
    $service: String!
  ) {
    llm_models
  }
`;
export interface GetLLMModelsVariables {
  service: string;
}export const GETLLMSERVICES_QUERY = gql`
  query GetLLMServices {
    llm_services
  }
`;export const GETNODESPECIFICATION_QUERY = gql`
  query GetNodeSpecification(
    $type: String!
  ) {
    node_specification {
      type
      label
      category
      description
      input_handles
      output_handles
      properties
    }
  }
`;
export interface GetNodeSpecificationVariables {
  type: string;
}export const GETNODETYPES_QUERY = gql`
  query GetNodeTypes {
    node_types
  }
`;export const GETPERSON_QUERY = gql`
  query GetPerson(
    $id: ID!
  ) {
    person {
      id
      label
      type
      llm_config {
        service
        model
        api_key_id
        system_prompt
        temperature
      }
    }
  }
`;
export interface GetPersonVariables {
  id: string;
}export const GETPROMPTTEMPLATE_QUERY = gql`
  query GetPromptTemplate(
    $id: ID!
  ) {
    prompt_template {
      id
      name
      category
      description
      template
      variables
      examples
    }
  }
`;
export interface GetPromptTemplateVariables {
  id: string;
}export const GETPROMPTTEMPLATES_QUERY = gql`
  query GetPromptTemplates(
    $category: String
  ) {
    prompt_templates {
      id
      name
      category
      description
      template
      variables
    }
  }
`;
export interface GetPromptTemplatesVariables {
  category?: string;
}export const GETSUPPORTEDFORMATS_QUERY = gql`
  query GetSupportedFormats {
    supported_formats
  }
`;export const GETSYSTEMINFO_QUERY = gql`
  query GetSystemInfo {
    system_info {
      version
      environment
      api_version
      uptime
    }
  }
`;export const HEALTHCHECK_QUERY = gql`
  query HealthCheck {
    health {
      status
      checks
    }
  }
`;export const LISTCONVERSATIONS_QUERY = gql`
  query ListConversations(
    $limit: Int, 
    $offset: Int
  ) {
    conversations {
      id
      title
      created
      updated
      message_count
    }
  }
`;
export interface ListConversationsVariables {
  limit?: number;
  offset?: number;
}export const LISTDIAGRAMS_QUERY = gql`
  query ListDiagrams(
    $filter: DiagramFilterInput, 
    $limit: Int, 
    $offset: Int
  ) {
    diagrams {
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
    $diagram_id: ID, 
    $status: ExecutionStatus, 
    $limit: Int, 
    $offset: Int
  ) {
    executions {
      id
      status
      phase
      diagram_id
      start_time
      end_time
      error
    }
  }
`;
export interface ListExecutionsVariables {
  diagram_id?: string;
  status?: ExecutionStatus;
  limit?: number;
  offset?: number;
}export const LISTFILES_QUERY = gql`
  query ListFiles(
    $path: String
  ) {
    files {
      name
      path
      size
      modified
      is_directory
    }
  }
`;
export interface ListFilesVariables {
  path?: string;
}export const LISTPERSONS_QUERY = gql`
  query ListPersons(
    $filter: PersonFilterInput, 
    $limit: Int, 
    $offset: Int
  ) {
    persons {
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
  filter?: PersonFilterInput;
  limit?: number;
  offset?: number;
}export const EXECUTIONUPDATES_SUBSCRIPTION = gql`
  subscription ExecutionUpdates(
    $execution_id: ID!
  ) {
    execution_updates {
      execution_id
      status
      phase
      node_updates
      timestamp
    }
  }
`;
export interface ExecutionUpdatesVariables {
  execution_id: string;
}export const QUERIES = {
  GETAPIKEY: GETAPIKEY_QUERY,
  GETAPIKEYS: GETAPIKEYS_QUERY,
  GETAVAILABLEMODELS: GETAVAILABLEMODELS_QUERY,
  GETCONVERSATION: GETCONVERSATION_QUERY,
  GETDIAGRAM: GETDIAGRAM_QUERY,
  GETEXECUTION: GETEXECUTION_QUERY,
  GETFILE: GETFILE_QUERY,
  GETLLMMODELS: GETLLMMODELS_QUERY,
  GETLLMSERVICES: GETLLMSERVICES_QUERY,
  GETNODESPECIFICATION: GETNODESPECIFICATION_QUERY,
  GETNODETYPES: GETNODETYPES_QUERY,
  GETPERSON: GETPERSON_QUERY,
  GETPROMPTTEMPLATE: GETPROMPTTEMPLATE_QUERY,
  GETPROMPTTEMPLATES: GETPROMPTTEMPLATES_QUERY,
  GETSUPPORTEDFORMATS: GETSUPPORTEDFORMATS_QUERY,
  GETSYSTEMINFO: GETSYSTEMINFO_QUERY,
  HEALTHCHECK: HEALTHCHECK_QUERY,
  LISTCONVERSATIONS: LISTCONVERSATIONS_QUERY,
  LISTDIAGRAMS: LISTDIAGRAMS_QUERY,
  LISTEXECUTIONS: LISTEXECUTIONS_QUERY,
  LISTFILES: LISTFILES_QUERY,
  LISTPERSONS: LISTPERSONS_QUERY
} as const;

export const MUTATIONS = {
  ADDMESSAGE: ADDMESSAGE_MUTATION,
  CANCELEXECUTION: CANCELEXECUTION_MUTATION,
  CONVERTFORMAT: CONVERTFORMAT_MUTATION,
  CREATEAPIKEY: CREATEAPIKEY_MUTATION,
  CREATECONVERSATION: CREATECONVERSATION_MUTATION,
  CREATEDIAGRAM: CREATEDIAGRAM_MUTATION,
  CREATEFILE: CREATEFILE_MUTATION,
  CREATEPERSON: CREATEPERSON_MUTATION,
  CREATEPROMPTTEMPLATE: CREATEPROMPTTEMPLATE_MUTATION,
  DELETEAPIKEY: DELETEAPIKEY_MUTATION,
  DELETECONVERSATION: DELETECONVERSATION_MUTATION,
  DELETEDIAGRAM: DELETEDIAGRAM_MUTATION,
  DELETEFILE: DELETEFILE_MUTATION,
  DELETEPERSON: DELETEPERSON_MUTATION,
  DELETEPROMPTTEMPLATE: DELETEPROMPTTEMPLATE_MUTATION,
  EXECUTEDIAGRAM: EXECUTEDIAGRAM_MUTATION,
  RENDERPROMPT: RENDERPROMPT_MUTATION,
  TESTAPIKEY: TESTAPIKEY_MUTATION,
  UPDATEFILE: UPDATEFILE_MUTATION,
  UPDATEPERSON: UPDATEPERSON_MUTATION,
  UPDATEPROMPTTEMPLATE: UPDATEPROMPTTEMPLATE_MUTATION,
  VALIDATEFORMAT: VALIDATEFORMAT_MUTATION,
  VALIDATENODE: VALIDATENODE_MUTATION
} as const;

export const SUBSCRIPTIONS = {
  EXECUTIONUPDATES: EXECUTIONUPDATES_SUBSCRIPTION
} as const;export type QueryName = keyof typeof QUERIES;
export type MutationName = keyof typeof MUTATIONS;
export type SubscriptionName = keyof typeof SUBSCRIPTIONS;export const OPERATION_METADATA = {
  AddMessage: {
    type: 'mutation',
    entity: 'Conversation',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CancelExecution: {
    type: 'mutation',
    entity: 'Execution',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ConvertFormat: {
    type: 'mutation',
    entity: 'Format',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CreateApiKey: {
    type: 'mutation',
    entity: 'ApiKey',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CreateConversation: {
    type: 'mutation',
    entity: 'Conversation',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CreateDiagram: {
    type: 'mutation',
    entity: 'Diagram',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CreateFile: {
    type: 'mutation',
    entity: 'File',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CreatePerson: {
    type: 'mutation',
    entity: 'Person',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  CreatePromptTemplate: {
    type: 'mutation',
    entity: 'Prompt',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  DeleteApiKey: {
    type: 'mutation',
    entity: 'ApiKey',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  DeleteConversation: {
    type: 'mutation',
    entity: 'Conversation',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  DeleteDiagram: {
    type: 'mutation',
    entity: 'Diagram',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  DeleteFile: {
    type: 'mutation',
    entity: 'File',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  DeletePerson: {
    type: 'mutation',
    entity: 'Person',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  DeletePromptTemplate: {
    type: 'mutation',
    entity: 'Prompt',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ExecuteDiagram: {
    type: 'mutation',
    entity: 'Diagram',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  RenderPrompt: {
    type: 'mutation',
    entity: 'Prompt',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  TestApiKey: {
    type: 'mutation',
    entity: 'ApiKey',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  UpdateFile: {
    type: 'mutation',
    entity: 'File',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  UpdatePerson: {
    type: 'mutation',
    entity: 'Person',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  UpdatePromptTemplate: {
    type: 'mutation',
    entity: 'Prompt',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ValidateFormat: {
    type: 'mutation',
    entity: 'Format',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ValidateNode: {
    type: 'mutation',
    entity: 'Node',
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
  GetConversation: {
    type: 'query',
    entity: 'Conversation',
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
  GetFile: {
    type: 'query',
    entity: 'File',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetLLMModels: {
    type: 'query',
    entity: 'System',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetLLMServices: {
    type: 'query',
    entity: 'System',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetNodeSpecification: {
    type: 'query',
    entity: 'Node',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetNodeTypes: {
    type: 'query',
    entity: 'Node',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetPerson: {
    type: 'query',
    entity: 'Person',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetPromptTemplate: {
    type: 'query',
    entity: 'Prompt',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  GetPromptTemplates: {
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
  ListFiles: {
    type: 'query',
    entity: 'File',
    operation: '',
    fieldPreset: 'STANDARD',
  },
  ListPersons: {
    type: 'query',
    entity: 'Person',
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