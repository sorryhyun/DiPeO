import type { NodeType } from '@dipeo/domain-models';
import type { HandleDirection } from '@dipeo/domain-models';
import type { HandleLabel } from '@dipeo/domain-models';
import type { DataType } from '@dipeo/domain-models';
import type { LLMService } from '@dipeo/domain-models';
import type { DiagramFormat } from '@dipeo/domain-models';
import type { ExecutionStatus } from '@dipeo/domain-models';
import type { ContentType } from '@dipeo/domain-models';
import type { ApiKeyID } from '@dipeo/domain-models';
import type { ArrowID } from '@dipeo/domain-models';
import type { DiagramID } from '@dipeo/domain-models';
import type { ExecutionID } from '@dipeo/domain-models';
import type { HandleID } from '@dipeo/domain-models';
import type { NodeID } from '@dipeo/domain-models';
import type { PersonID } from '@dipeo/domain-models';
import { gql } from '@apollo/client';
import * as Apollo from '@apollo/client';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
const defaultOptions = {} as const;
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /** Unique identifier for apikey */
  ApiKeyID: { input: ApiKeyID; output: ApiKeyID; }
  /** Unique identifier for arrow */
  ArrowID: { input: ArrowID; output: ArrowID; }
  /** Date with time (isoformat) */
  DateTime: { input: any; output: any; }
  /** Unique identifier for diagram */
  DiagramID: { input: DiagramID; output: DiagramID; }
  /** Unique identifier for execution */
  ExecutionID: { input: ExecutionID; output: ExecutionID; }
  /** Unique identifier for handle */
  HandleID: { input: HandleID; output: HandleID; }
  /** Arbitrary JSON data */
  JSONScalar: { input: any; output: any; }
  /** Unique identifier for node */
  NodeID: { input: NodeID; output: NodeID; }
  /** Unique identifier for person */
  PersonID: { input: PersonID; output: PersonID; }
  Upload: { input: any; output: any; }
};

export enum APIServiceType {
  ANTHROPIC = 'ANTHROPIC',
  BEDROCK = 'BEDROCK',
  DEEPSEEK = 'DEEPSEEK',
  GEMINI = 'GEMINI',
  GITHUB = 'GITHUB',
  GOOGLE = 'GOOGLE',
  GOOGLE_SEARCH = 'GOOGLE_SEARCH',
  JIRA = 'JIRA',
  NOTION = 'NOTION',
  OPENAI = 'OPENAI',
  SLACK = 'SLACK',
  VERTEX = 'VERTEX'
}

export type ApiKeyResult = {
  __typename?: 'ApiKeyResult';
  api_key?: Maybe<DomainApiKeyType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export { ContentType };

export type CreateApiKeyInput = {
  key: Scalars['String']['input'];
  label: Scalars['String']['input'];
  service: APIServiceType;
};

export type CreateDiagramInput = {
  author?: InputMaybe<Scalars['String']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  tags?: Array<Scalars['String']['input']>;
};

export type CreateNodeInput = {
  data: Scalars['JSONScalar']['input'];
  position: Vec2Input;
  type: NodeType;
};

export type CreatePersonInput = {
  label: Scalars['String']['input'];
  llm_config: PersonLLMConfigInput;
  type?: Scalars['String']['input'];
};

export { DataType };

export type DeleteResult = {
  __typename?: 'DeleteResult';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type DiagramConvertResult = {
  __typename?: 'DiagramConvertResult';
  content?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  filename?: Maybe<Scalars['String']['output']>;
  format?: Maybe<Scalars['String']['output']>;
  message: Scalars['String']['output'];
  success: Scalars['Boolean']['output'];
};

export type DiagramFilterInput = {
  author?: InputMaybe<Scalars['String']['input']>;
  created_after?: InputMaybe<Scalars['DateTime']['input']>;
  created_before?: InputMaybe<Scalars['DateTime']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  tags?: InputMaybe<Array<Scalars['String']['input']>>;
};

export { DiagramFormat };

export type DiagramFormatInfo = {
  __typename?: 'DiagramFormatInfo';
  description?: Maybe<Scalars['String']['output']>;
  extension: Scalars['String']['output'];
  format: Scalars['String']['output'];
  name: Scalars['String']['output'];
  supports_export: Scalars['Boolean']['output'];
  supports_import: Scalars['Boolean']['output'];
};

export type DiagramMetadataType = {
  __typename?: 'DiagramMetadataType';
  author?: Maybe<Scalars['String']['output']>;
  created: Scalars['String']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  modified: Scalars['String']['output'];
  name?: Maybe<Scalars['String']['output']>;
  tags?: Maybe<Array<Scalars['String']['output']>>;
  version: Scalars['String']['output'];
};

export type DiagramResult = {
  __typename?: 'DiagramResult';
  diagram?: Maybe<DomainDiagramType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type DiagramValidationResult = {
  __typename?: 'DiagramValidationResult';
  arrow_count?: Maybe<Scalars['Int']['output']>;
  errors: Array<Scalars['String']['output']>;
  is_valid: Scalars['Boolean']['output'];
  node_count?: Maybe<Scalars['Int']['output']>;
  person_count?: Maybe<Scalars['Int']['output']>;
};

export type DomainApiKeyType = {
  __typename?: 'DomainApiKeyType';
  id: Scalars['ApiKeyID']['output'];
  key?: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  service: APIServiceType;
};

export type DomainArrowType = {
  __typename?: 'DomainArrowType';
  content_type?: Maybe<ContentType>;
  data?: Maybe<Scalars['JSONScalar']['output']>;
  id: Scalars['ArrowID']['output'];
  label?: Maybe<Scalars['String']['output']>;
  source: Scalars['HandleID']['output'];
  target: Scalars['HandleID']['output'];
};

export type DomainDiagramType = {
  __typename?: 'DomainDiagramType';
  arrowCount: Scalars['Int']['output'];
  arrows: Array<DomainArrowType>;
  handles: Array<DomainHandleType>;
  metadata?: Maybe<DiagramMetadataType>;
  nodeCount: Scalars['Int']['output'];
  nodes: Array<DomainNodeType>;
  persons: Array<DomainPersonType>;
};

export type DomainHandleType = {
  __typename?: 'DomainHandleType';
  data_type: DataType;
  direction: HandleDirection;
  id: Scalars['HandleID']['output'];
  label: HandleLabel;
  node_id: Scalars['NodeID']['output'];
  position?: Maybe<Scalars['String']['output']>;
};

export type DomainNodeType = {
  __typename?: 'DomainNodeType';
  data: Scalars['JSONScalar']['output'];
  id: Scalars['NodeID']['output'];
  position: Vec2Type;
  type: NodeType;
};

export type DomainPersonType = {
  __typename?: 'DomainPersonType';
  id: Scalars['PersonID']['output'];
  label: Scalars['String']['output'];
  llm_config: PersonLLMConfigType;
  type: Scalars['String']['output'];
};

export type ExecuteDiagramInput = {
  debug_mode?: InputMaybe<Scalars['Boolean']['input']>;
  diagram_data?: InputMaybe<Scalars['JSONScalar']['input']>;
  diagram_id?: InputMaybe<Scalars['DiagramID']['input']>;
  max_iterations?: InputMaybe<Scalars['Int']['input']>;
  timeout_seconds?: InputMaybe<Scalars['Int']['input']>;
  variables?: InputMaybe<Scalars['JSONScalar']['input']>;
};

export type ExecutionControlInput = {
  action: Scalars['String']['input'];
  execution_id: Scalars['ExecutionID']['input'];
  reason?: InputMaybe<Scalars['String']['input']>;
};

export type ExecutionFilterInput = {
  diagram_id?: InputMaybe<Scalars['DiagramID']['input']>;
  started_after?: InputMaybe<Scalars['DateTime']['input']>;
  started_before?: InputMaybe<Scalars['DateTime']['input']>;
  status?: InputMaybe<ExecutionStatus>;
};

export type ExecutionResult = {
  __typename?: 'ExecutionResult';
  error?: Maybe<Scalars['String']['output']>;
  execution?: Maybe<ExecutionStateType>;
  execution_id?: Maybe<Scalars['ExecutionID']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type ExecutionStateType = {
  __typename?: 'ExecutionStateType';
  diagram_id?: Maybe<Scalars['String']['output']>;
  duration_seconds?: Maybe<Scalars['Float']['output']>;
  ended_at?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  exec_counts: Scalars['JSONScalar']['output'];
  executed_nodes: Array<Scalars['String']['output']>;
  id: Scalars['String']['output'];
  is_active?: Maybe<Scalars['Boolean']['output']>;
  node_outputs: Scalars['JSONScalar']['output'];
  node_states: Scalars['JSONScalar']['output'];
  started_at: Scalars['String']['output'];
  status: ExecutionStatus;
  token_usage: TokenUsageType;
  variables: Scalars['JSONScalar']['output'];
};

export { ExecutionStatus };

export type FileUploadResult = {
  __typename?: 'FileUploadResult';
  content_type?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  path?: Maybe<Scalars['String']['output']>;
  size_bytes?: Maybe<Scalars['Int']['output']>;
  success: Scalars['Boolean']['output'];
};

export { HandleDirection };

export { HandleLabel };

export type InteractivePrompt = {
  __typename?: 'InteractivePrompt';
  execution_id: Scalars['ExecutionID']['output'];
  node_id: Scalars['NodeID']['output'];
  prompt: Scalars['String']['output'];
  timeout_seconds?: Maybe<Scalars['Int']['output']>;
  timestamp: Scalars['DateTime']['output'];
};

export type InteractiveResponseInput = {
  execution_id: Scalars['ExecutionID']['input'];
  metadata?: InputMaybe<Scalars['JSONScalar']['input']>;
  node_id: Scalars['NodeID']['input'];
  response: Scalars['String']['input'];
};

export { LLMService };

export type Mutation = {
  __typename?: 'Mutation';
  clear_conversations: DeleteResult;
  control_execution: ExecutionResult;
  /** Convert a diagram to a different format */
  convert_diagram: DiagramConvertResult;
  create_api_key: ApiKeyResult;
  create_diagram: DiagramResult;
  create_node: NodeResult;
  create_person: PersonResult;
  delete_api_key: DeleteResult;
  delete_diagram: DeleteResult;
  delete_node: DeleteResult;
  delete_person: DeleteResult;
  execute_diagram: ExecutionResult;
  initialize_model: PersonResult;
  submit_interactive_response: ExecutionResult;
  test_api_key: TestApiKeyResult;
  update_node: NodeResult;
  update_person: PersonResult;
  /** Upload a file to the server */
  upload_file: FileUploadResult;
  /** Validate a diagram structure */
  validate_diagram: DiagramValidationResult;
};


export type Mutationcontrol_executionArgs = {
  data: ExecutionControlInput;
};


export type Mutationconvert_diagramArgs = {
  content: Scalars['JSONScalar']['input'];
  include_metadata?: Scalars['Boolean']['input'];
  target_format?: DiagramFormat;
};


export type Mutationcreate_api_keyArgs = {
  input: CreateApiKeyInput;
};


export type Mutationcreate_diagramArgs = {
  input: CreateDiagramInput;
};


export type Mutationcreate_nodeArgs = {
  diagram_id: Scalars['DiagramID']['input'];
  input_data: CreateNodeInput;
};


export type Mutationcreate_personArgs = {
  diagram_id: Scalars['DiagramID']['input'];
  person_input: CreatePersonInput;
};


export type Mutationdelete_api_keyArgs = {
  id: Scalars['ApiKeyID']['input'];
};


export type Mutationdelete_diagramArgs = {
  id: Scalars['DiagramID']['input'];
};


export type Mutationdelete_nodeArgs = {
  node_id: Scalars['NodeID']['input'];
};


export type Mutationdelete_personArgs = {
  person_id: Scalars['PersonID']['input'];
};


export type Mutationexecute_diagramArgs = {
  data: ExecuteDiagramInput;
};


export type Mutationinitialize_modelArgs = {
  api_key_id: Scalars['ApiKeyID']['input'];
  label?: Scalars['String']['input'];
  model: Scalars['String']['input'];
  person_id: Scalars['PersonID']['input'];
};


export type Mutationsubmit_interactive_responseArgs = {
  data: InteractiveResponseInput;
};


export type Mutationtest_api_keyArgs = {
  id: Scalars['ApiKeyID']['input'];
};


export type Mutationupdate_nodeArgs = {
  input_data: UpdateNodeInput;
};


export type Mutationupdate_personArgs = {
  person_input: UpdatePersonInput;
};


export type Mutationupload_fileArgs = {
  category?: Scalars['String']['input'];
  file: Scalars['Upload']['input'];
};


export type Mutationvalidate_diagramArgs = {
  diagram_content: Scalars['JSONScalar']['input'];
};

export type NodeExecution = {
  __typename?: 'NodeExecution';
  error?: Maybe<Scalars['String']['output']>;
  execution_id: Scalars['ExecutionID']['output'];
  node_id: Scalars['NodeID']['output'];
  node_type: NodeType;
  output?: Maybe<Scalars['JSONScalar']['output']>;
  progress?: Maybe<Scalars['String']['output']>;
  status: Scalars['String']['output'];
  timestamp: Scalars['DateTime']['output'];
  tokens_used?: Maybe<Scalars['Int']['output']>;
};

export type NodeResult = {
  __typename?: 'NodeResult';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  node?: Maybe<DomainNodeType>;
  success: Scalars['Boolean']['output'];
};

export { NodeType };

export type PersonLLMConfigInput = {
  api_key_id: Scalars['ApiKeyID']['input'];
  model: Scalars['String']['input'];
  service: LLMService;
  system_prompt?: InputMaybe<Scalars['String']['input']>;
};

export type PersonLLMConfigType = {
  __typename?: 'PersonLLMConfigType';
  api_key_id: Scalars['String']['output'];
  model: Scalars['String']['output'];
  service: LLMService;
  system_prompt?: Maybe<Scalars['String']['output']>;
};

export type PersonResult = {
  __typename?: 'PersonResult';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  person?: Maybe<DomainPersonType>;
  success: Scalars['Boolean']['output'];
};

export type Query = {
  __typename?: 'Query';
  api_key?: Maybe<DomainApiKeyType>;
  api_keys: Array<DomainApiKeyType>;
  available_models: Array<Scalars['String']['output']>;
  conversations: Scalars['JSONScalar']['output'];
  diagram?: Maybe<DomainDiagramType>;
  diagrams: Array<DomainDiagramType>;
  execution?: Maybe<ExecutionStateType>;
  execution_capabilities: Scalars['JSONScalar']['output'];
  execution_order: Scalars['JSONScalar']['output'];
  executions: Array<ExecutionStateType>;
  health: Scalars['JSONScalar']['output'];
  person?: Maybe<DomainPersonType>;
  persons: Array<DomainPersonType>;
  prompt_file: Scalars['JSONScalar']['output'];
  prompt_files: Array<Scalars['JSONScalar']['output']>;
  supported_formats: Array<DiagramFormatInfo>;
  system_info: Scalars['JSONScalar']['output'];
};


export type Queryapi_keyArgs = {
  id: Scalars['ApiKeyID']['input'];
};


export type Queryapi_keysArgs = {
  service?: InputMaybe<Scalars['String']['input']>;
};


export type Queryavailable_modelsArgs = {
  api_key_id: Scalars['ApiKeyID']['input'];
  service: Scalars['String']['input'];
};


export type QueryconversationsArgs = {
  execution_id?: InputMaybe<Scalars['ExecutionID']['input']>;
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
  person_id?: InputMaybe<Scalars['PersonID']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  show_forgotten?: Scalars['Boolean']['input'];
  since?: InputMaybe<Scalars['DateTime']['input']>;
};


export type QuerydiagramArgs = {
  id: Scalars['DiagramID']['input'];
};


export type QuerydiagramsArgs = {
  filter?: InputMaybe<DiagramFilterInput>;
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
};


export type QueryexecutionArgs = {
  id: Scalars['ExecutionID']['input'];
};


export type Queryexecution_orderArgs = {
  execution_id: Scalars['ExecutionID']['input'];
};


export type QueryexecutionsArgs = {
  filter?: InputMaybe<ExecutionFilterInput>;
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
};


export type QuerypersonArgs = {
  id: Scalars['PersonID']['input'];
};


export type QuerypersonsArgs = {
  limit?: Scalars['Int']['input'];
};


export type Queryprompt_fileArgs = {
  filename: Scalars['String']['input'];
};

export type Subscription = {
  __typename?: 'Subscription';
  diagram_changes: DomainDiagramType;
  execution_events: ExecutionStatus;
  execution_updates: ExecutionStateType;
  interactive_prompts?: Maybe<InteractivePrompt>;
  node_updates: NodeExecution;
};


export type Subscriptiondiagram_changesArgs = {
  diagram_id: Scalars['DiagramID']['input'];
};


export type Subscriptionexecution_eventsArgs = {
  execution_id: Scalars['ExecutionID']['input'];
};


export type Subscriptionexecution_updatesArgs = {
  execution_id: Scalars['ExecutionID']['input'];
};


export type Subscriptioninteractive_promptsArgs = {
  execution_id: Scalars['ExecutionID']['input'];
};


export type Subscriptionnode_updatesArgs = {
  execution_id: Scalars['ExecutionID']['input'];
  node_types?: InputMaybe<Array<NodeType>>;
};

export type TestApiKeyResult = {
  __typename?: 'TestApiKeyResult';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  model_info?: Maybe<Scalars['JSONScalar']['output']>;
  success: Scalars['Boolean']['output'];
};

export type TokenUsageType = {
  __typename?: 'TokenUsageType';
  cached?: Maybe<Scalars['Int']['output']>;
  input: Scalars['Int']['output'];
  output: Scalars['Int']['output'];
  total?: Maybe<Scalars['Int']['output']>;
};

export type UpdateNodeInput = {
  data?: InputMaybe<Scalars['JSONScalar']['input']>;
  position?: InputMaybe<Vec2Input>;
};

export type UpdatePersonInput = {
  label?: InputMaybe<Scalars['String']['input']>;
  llm_config?: InputMaybe<PersonLLMConfigInput>;
};

export type Vec2Input = {
  x: Scalars['Float']['input'];
  y: Scalars['Float']['input'];
};

export type Vec2Type = {
  __typename?: 'Vec2Type';
  x: Scalars['Int']['output'];
  y: Scalars['Int']['output'];
};

export type GetApiKeysQueryVariables = Exact<{
  service?: InputMaybe<Scalars['String']['input']>;
}>;


export type GetApiKeysQuery = { __typename?: 'Query', api_keys: Array<{ __typename?: 'DomainApiKeyType', id: ApiKeyID, label: string, service: APIServiceType, key?: string | null }> };

export type GetApiKeyQueryVariables = Exact<{
  id: Scalars['ApiKeyID']['input'];
}>;


export type GetApiKeyQuery = { __typename?: 'Query', api_key?: { __typename?: 'DomainApiKeyType', id: ApiKeyID, label: string, service: APIServiceType } | null };

export type GetAvailableModelsQueryVariables = Exact<{
  service: Scalars['String']['input'];
  apiKeyId: Scalars['ApiKeyID']['input'];
}>;


export type GetAvailableModelsQuery = { __typename?: 'Query', available_models: Array<string> };

export type CreateApiKeyMutationVariables = Exact<{
  input: CreateApiKeyInput;
}>;


export type CreateApiKeyMutation = { __typename?: 'Mutation', create_api_key: { __typename?: 'ApiKeyResult', success: boolean, message?: string | null, error?: string | null, api_key?: { __typename?: 'DomainApiKeyType', id: ApiKeyID, label: string, service: APIServiceType } | null } };

export type TestApiKeyMutationVariables = Exact<{
  id: Scalars['ApiKeyID']['input'];
}>;


export type TestApiKeyMutation = { __typename?: 'Mutation', test_api_key: { __typename?: 'TestApiKeyResult', success: boolean, message?: string | null, error?: string | null } };

export type DeleteApiKeyMutationVariables = Exact<{
  id: Scalars['ApiKeyID']['input'];
}>;


export type DeleteApiKeyMutation = { __typename?: 'Mutation', delete_api_key: { __typename?: 'DeleteResult', success: boolean, message?: string | null } };

export type GetConversationsQueryVariables = Exact<{
  person_id?: InputMaybe<Scalars['PersonID']['input']>;
  execution_id?: InputMaybe<Scalars['ExecutionID']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  show_forgotten?: InputMaybe<Scalars['Boolean']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  since?: InputMaybe<Scalars['DateTime']['input']>;
}>;


export type GetConversationsQuery = { __typename?: 'Query', conversations: any };

export type ClearConversationsMutationVariables = Exact<{ [key: string]: never; }>;


export type ClearConversationsMutation = { __typename?: 'Mutation', clear_conversations: { __typename?: 'DeleteResult', success: boolean, message?: string | null } };

export type GetDiagramQueryVariables = Exact<{
  id: Scalars['DiagramID']['input'];
}>;


export type GetDiagramQuery = { __typename?: 'Query', diagram?: { __typename?: 'DomainDiagramType', nodes: Array<{ __typename?: 'DomainNodeType', id: NodeID, type: NodeType, data: any, position: { __typename?: 'Vec2Type', x: number, y: number } }>, handles: Array<{ __typename?: 'DomainHandleType', id: HandleID, node_id: NodeID, label: HandleLabel, direction: HandleDirection, data_type: DataType, position?: string | null }>, arrows: Array<{ __typename?: 'DomainArrowType', id: ArrowID, source: HandleID, target: HandleID, content_type?: ContentType | null, label?: string | null, data?: any | null }>, persons: Array<{ __typename?: 'DomainPersonType', id: PersonID, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } }>, metadata?: { __typename?: 'DiagramMetadataType', id?: string | null, name?: string | null, description?: string | null, version: string, created: string, modified: string, author?: string | null, tags?: Array<string> | null } | null } | null };

export type ListDiagramsQueryVariables = Exact<{
  filter?: InputMaybe<DiagramFilterInput>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ListDiagramsQuery = { __typename?: 'Query', diagrams: Array<{ __typename?: 'DomainDiagramType', nodeCount: number, arrowCount: number, metadata?: { __typename?: 'DiagramMetadataType', id?: string | null, name?: string | null, description?: string | null, author?: string | null, created: string, modified: string, tags?: Array<string> | null } | null }> };

export type CreateDiagramMutationVariables = Exact<{
  input: CreateDiagramInput;
}>;


export type CreateDiagramMutation = { __typename?: 'Mutation', create_diagram: { __typename?: 'DiagramResult', success: boolean, message?: string | null, error?: string | null, diagram?: { __typename?: 'DomainDiagramType', metadata?: { __typename?: 'DiagramMetadataType', id?: string | null, name?: string | null } | null } | null } };

export type ExecuteDiagramMutationVariables = Exact<{
  data: ExecuteDiagramInput;
}>;


export type ExecuteDiagramMutation = { __typename?: 'Mutation', execute_diagram: { __typename?: 'ExecutionResult', success: boolean, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionStateType', id: string } | null } };

export type DeleteDiagramMutationVariables = Exact<{
  id: Scalars['DiagramID']['input'];
}>;


export type DeleteDiagramMutation = { __typename?: 'Mutation', delete_diagram: { __typename?: 'DeleteResult', success: boolean, message?: string | null, error?: string | null } };

export type GetExecutionQueryVariables = Exact<{
  id: Scalars['ExecutionID']['input'];
}>;


export type GetExecutionQuery = { __typename?: 'Query', execution?: { __typename?: 'ExecutionStateType', id: string, status: ExecutionStatus, diagram_id?: string | null, started_at: string, ended_at?: string | null, node_states: any, node_outputs: any, variables: any, error?: string | null, duration_seconds?: number | null, is_active?: boolean | null, token_usage: { __typename?: 'TokenUsageType', input: number, output: number, cached?: number | null } } | null };

export type ListExecutionsQueryVariables = Exact<{
  filter?: InputMaybe<ExecutionFilterInput>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ListExecutionsQuery = { __typename?: 'Query', executions: Array<{ __typename?: 'ExecutionStateType', id: string, status: ExecutionStatus, diagram_id?: string | null, started_at: string, ended_at?: string | null, is_active?: boolean | null, duration_seconds?: number | null }> };

export type ExecutionUpdatesSubscriptionVariables = Exact<{
  executionId: Scalars['ExecutionID']['input'];
}>;


export type ExecutionUpdatesSubscription = { __typename?: 'Subscription', execution_updates: { __typename?: 'ExecutionStateType', id: string, status: ExecutionStatus, node_states: any, node_outputs: any, error?: string | null, token_usage: { __typename?: 'TokenUsageType', input: number, output: number, cached?: number | null } } };

export type NodeUpdatesSubscriptionVariables = Exact<{
  executionId: Scalars['ExecutionID']['input'];
  nodeTypes?: InputMaybe<Array<NodeType> | NodeType>;
}>;


export type NodeUpdatesSubscription = { __typename?: 'Subscription', node_updates: { __typename?: 'NodeExecution', execution_id: ExecutionID, node_id: NodeID, node_type: NodeType, status: string, progress?: string | null, output?: any | null, error?: string | null, tokens_used?: number | null, timestamp: any } };

export type InteractivePromptsSubscriptionVariables = Exact<{
  executionId: Scalars['ExecutionID']['input'];
}>;


export type InteractivePromptsSubscription = { __typename?: 'Subscription', interactive_prompts?: { __typename?: 'InteractivePrompt', execution_id: ExecutionID, node_id: NodeID, prompt: string, timeout_seconds?: number | null, timestamp: any } | null };

export type ControlExecutionMutationVariables = Exact<{
  data: ExecutionControlInput;
}>;


export type ControlExecutionMutation = { __typename?: 'Mutation', control_execution: { __typename?: 'ExecutionResult', success: boolean, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionStateType', id: string, status: ExecutionStatus } | null } };

export type SubmitInteractiveResponseMutationVariables = Exact<{
  data: InteractiveResponseInput;
}>;


export type SubmitInteractiveResponseMutation = { __typename?: 'Mutation', submit_interactive_response: { __typename?: 'ExecutionResult', success: boolean, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionStateType', id: string, status: ExecutionStatus, node_states: any } | null } };

export type UploadFileMutationVariables = Exact<{
  file: Scalars['Upload']['input'];
  category?: Scalars['String']['input'];
}>;


export type UploadFileMutation = { __typename?: 'Mutation', upload_file: { __typename?: 'FileUploadResult', success: boolean, path?: string | null, size_bytes?: number | null, content_type?: string | null, message?: string | null, error?: string | null } };

export type ValidateDiagramMutationVariables = Exact<{
  diagramContent: Scalars['JSONScalar']['input'];
}>;


export type ValidateDiagramMutation = { __typename?: 'Mutation', validate_diagram: { __typename?: 'DiagramValidationResult', is_valid: boolean, errors: Array<string>, node_count?: number | null, arrow_count?: number | null, person_count?: number | null } };

export type ConvertDiagramMutationVariables = Exact<{
  content: Scalars['JSONScalar']['input'];
  targetFormat?: InputMaybe<DiagramFormat>;
  includeMetadata?: InputMaybe<Scalars['Boolean']['input']>;
}>;


export type ConvertDiagramMutation = { __typename?: 'Mutation', convert_diagram: { __typename?: 'DiagramConvertResult', success: boolean, message: string, error?: string | null, content?: string | null, format?: string | null, filename?: string | null } };

export type GetSupportedFormatsQueryVariables = Exact<{ [key: string]: never; }>;


export type GetSupportedFormatsQuery = { __typename?: 'Query', supported_formats: Array<{ __typename?: 'DiagramFormatInfo', format: string, name: string, extension: string, supports_export: boolean, supports_import: boolean, description?: string | null }> };

export type CreateNodeMutationVariables = Exact<{
  diagramId: Scalars['DiagramID']['input'];
  inputData: CreateNodeInput;
}>;


export type CreateNodeMutation = { __typename?: 'Mutation', create_node: { __typename?: 'NodeResult', success: boolean, message?: string | null, error?: string | null, node?: { __typename?: 'DomainNodeType', id: NodeID, type: NodeType, data: any, position: { __typename?: 'Vec2Type', x: number, y: number } } | null } };

export type UpdateNodeMutationVariables = Exact<{
  inputData: UpdateNodeInput;
}>;


export type UpdateNodeMutation = { __typename?: 'Mutation', update_node: { __typename?: 'NodeResult', success: boolean, message?: string | null, error?: string | null, node?: { __typename?: 'DomainNodeType', id: NodeID, type: NodeType, data: any, position: { __typename?: 'Vec2Type', x: number, y: number } } | null } };

export type DeleteNodeMutationVariables = Exact<{
  nodeId: Scalars['NodeID']['input'];
}>;


export type DeleteNodeMutation = { __typename?: 'Mutation', delete_node: { __typename?: 'DeleteResult', success: boolean, message?: string | null, error?: string | null } };

export type GetPersonQueryVariables = Exact<{
  id: Scalars['PersonID']['input'];
}>;


export type GetPersonQuery = { __typename?: 'Query', person?: { __typename?: 'DomainPersonType', id: PersonID, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } } | null };

export type GetPersonsQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Int']['input']>;
}>;


export type GetPersonsQuery = { __typename?: 'Query', persons: Array<{ __typename?: 'DomainPersonType', id: PersonID, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } }> };

export type CreatePersonMutationVariables = Exact<{
  diagramId: Scalars['DiagramID']['input'];
  personInput: CreatePersonInput;
}>;


export type CreatePersonMutation = { __typename?: 'Mutation', create_person: { __typename?: 'PersonResult', success: boolean, message?: string | null, error?: string | null, person?: { __typename?: 'DomainPersonType', id: PersonID, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } } | null } };

export type UpdatePersonMutationVariables = Exact<{
  personInput: UpdatePersonInput;
}>;


export type UpdatePersonMutation = { __typename?: 'Mutation', update_person: { __typename?: 'PersonResult', success: boolean, message?: string | null, error?: string | null, person?: { __typename?: 'DomainPersonType', id: PersonID, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } } | null } };

export type DeletePersonMutationVariables = Exact<{
  personId: Scalars['PersonID']['input'];
}>;


export type DeletePersonMutation = { __typename?: 'Mutation', delete_person: { __typename?: 'DeleteResult', success: boolean, message?: string | null, error?: string | null } };

export type InitializeModelMutationVariables = Exact<{
  personId: Scalars['PersonID']['input'];
  apiKeyId: Scalars['ApiKeyID']['input'];
  model: Scalars['String']['input'];
  label: Scalars['String']['input'];
}>;


export type InitializeModelMutation = { __typename?: 'Mutation', initialize_model: { __typename?: 'PersonResult', success: boolean, message?: string | null, error?: string | null, person?: { __typename?: 'DomainPersonType', id: PersonID, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } } | null } };

export type GetPromptFilesQueryVariables = Exact<{ [key: string]: never; }>;


export type GetPromptFilesQuery = { __typename?: 'Query', prompt_files: Array<any> };

export type GetPromptFileQueryVariables = Exact<{
  filename: Scalars['String']['input'];
}>;


export type GetPromptFileQuery = { __typename?: 'Query', prompt_file: any };

export type GetSystemInfoQueryVariables = Exact<{ [key: string]: never; }>;


export type GetSystemInfoQuery = { __typename?: 'Query', system_info: any };

export type ExecutionOrderQueryVariables = Exact<{
  executionId: Scalars['ExecutionID']['input'];
}>;


export type ExecutionOrderQuery = { __typename?: 'Query', execution_order: any };


export const GetApiKeysDocument = gql`
    query GetApiKeys($service: String) {
  api_keys(service: $service) {
    id
    label
    service
    key
  }
}
    `;

/**
 * __useGetApiKeysQuery__
 *
 * To run a query within a React component, call `useGetApiKeysQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetApiKeysQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetApiKeysQuery({
 *   variables: {
 *      service: // value for 'service'
 *   },
 * });
 */
export function useGetApiKeysQuery(baseOptions?: Apollo.QueryHookOptions<GetApiKeysQuery, GetApiKeysQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetApiKeysQuery, GetApiKeysQueryVariables>(GetApiKeysDocument, options);
      }
export function useGetApiKeysLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetApiKeysQuery, GetApiKeysQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetApiKeysQuery, GetApiKeysQueryVariables>(GetApiKeysDocument, options);
        }
export function useGetApiKeysSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetApiKeysQuery, GetApiKeysQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetApiKeysQuery, GetApiKeysQueryVariables>(GetApiKeysDocument, options);
        }
export type GetApiKeysQueryHookResult = ReturnType<typeof useGetApiKeysQuery>;
export type GetApiKeysLazyQueryHookResult = ReturnType<typeof useGetApiKeysLazyQuery>;
export type GetApiKeysSuspenseQueryHookResult = ReturnType<typeof useGetApiKeysSuspenseQuery>;
export type GetApiKeysQueryResult = Apollo.QueryResult<GetApiKeysQuery, GetApiKeysQueryVariables>;
export const GetApiKeyDocument = gql`
    query GetApiKey($id: ApiKeyID!) {
  api_key(id: $id) {
    id
    label
    service
  }
}
    `;

/**
 * __useGetApiKeyQuery__
 *
 * To run a query within a React component, call `useGetApiKeyQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetApiKeyQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetApiKeyQuery({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useGetApiKeyQuery(baseOptions: Apollo.QueryHookOptions<GetApiKeyQuery, GetApiKeyQueryVariables> & ({ variables: GetApiKeyQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetApiKeyQuery, GetApiKeyQueryVariables>(GetApiKeyDocument, options);
      }
export function useGetApiKeyLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetApiKeyQuery, GetApiKeyQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetApiKeyQuery, GetApiKeyQueryVariables>(GetApiKeyDocument, options);
        }
export function useGetApiKeySuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetApiKeyQuery, GetApiKeyQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetApiKeyQuery, GetApiKeyQueryVariables>(GetApiKeyDocument, options);
        }
export type GetApiKeyQueryHookResult = ReturnType<typeof useGetApiKeyQuery>;
export type GetApiKeyLazyQueryHookResult = ReturnType<typeof useGetApiKeyLazyQuery>;
export type GetApiKeySuspenseQueryHookResult = ReturnType<typeof useGetApiKeySuspenseQuery>;
export type GetApiKeyQueryResult = Apollo.QueryResult<GetApiKeyQuery, GetApiKeyQueryVariables>;
export const GetAvailableModelsDocument = gql`
    query GetAvailableModels($service: String!, $apiKeyId: ApiKeyID!) {
  available_models(service: $service, api_key_id: $apiKeyId)
}
    `;

/**
 * __useGetAvailableModelsQuery__
 *
 * To run a query within a React component, call `useGetAvailableModelsQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetAvailableModelsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetAvailableModelsQuery({
 *   variables: {
 *      service: // value for 'service'
 *      apiKeyId: // value for 'apiKeyId'
 *   },
 * });
 */
export function useGetAvailableModelsQuery(baseOptions: Apollo.QueryHookOptions<GetAvailableModelsQuery, GetAvailableModelsQueryVariables> & ({ variables: GetAvailableModelsQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetAvailableModelsQuery, GetAvailableModelsQueryVariables>(GetAvailableModelsDocument, options);
      }
export function useGetAvailableModelsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetAvailableModelsQuery, GetAvailableModelsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetAvailableModelsQuery, GetAvailableModelsQueryVariables>(GetAvailableModelsDocument, options);
        }
export function useGetAvailableModelsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetAvailableModelsQuery, GetAvailableModelsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetAvailableModelsQuery, GetAvailableModelsQueryVariables>(GetAvailableModelsDocument, options);
        }
export type GetAvailableModelsQueryHookResult = ReturnType<typeof useGetAvailableModelsQuery>;
export type GetAvailableModelsLazyQueryHookResult = ReturnType<typeof useGetAvailableModelsLazyQuery>;
export type GetAvailableModelsSuspenseQueryHookResult = ReturnType<typeof useGetAvailableModelsSuspenseQuery>;
export type GetAvailableModelsQueryResult = Apollo.QueryResult<GetAvailableModelsQuery, GetAvailableModelsQueryVariables>;
export const CreateApiKeyDocument = gql`
    mutation CreateApiKey($input: CreateApiKeyInput!) {
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
export type CreateApiKeyMutationFn = Apollo.MutationFunction<CreateApiKeyMutation, CreateApiKeyMutationVariables>;

/**
 * __useCreateApiKeyMutation__
 *
 * To run a mutation, you first call `useCreateApiKeyMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useCreateApiKeyMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [createApiKeyMutation, { data, loading, error }] = useCreateApiKeyMutation({
 *   variables: {
 *      input: // value for 'input'
 *   },
 * });
 */
export function useCreateApiKeyMutation(baseOptions?: Apollo.MutationHookOptions<CreateApiKeyMutation, CreateApiKeyMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<CreateApiKeyMutation, CreateApiKeyMutationVariables>(CreateApiKeyDocument, options);
      }
export type CreateApiKeyMutationHookResult = ReturnType<typeof useCreateApiKeyMutation>;
export type CreateApiKeyMutationResult = Apollo.MutationResult<CreateApiKeyMutation>;
export type CreateApiKeyMutationOptions = Apollo.BaseMutationOptions<CreateApiKeyMutation, CreateApiKeyMutationVariables>;
export const TestApiKeyDocument = gql`
    mutation TestApiKey($id: ApiKeyID!) {
  test_api_key(id: $id) {
    success
    message
    error
  }
}
    `;
export type TestApiKeyMutationFn = Apollo.MutationFunction<TestApiKeyMutation, TestApiKeyMutationVariables>;

/**
 * __useTestApiKeyMutation__
 *
 * To run a mutation, you first call `useTestApiKeyMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useTestApiKeyMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [testApiKeyMutation, { data, loading, error }] = useTestApiKeyMutation({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useTestApiKeyMutation(baseOptions?: Apollo.MutationHookOptions<TestApiKeyMutation, TestApiKeyMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<TestApiKeyMutation, TestApiKeyMutationVariables>(TestApiKeyDocument, options);
      }
export type TestApiKeyMutationHookResult = ReturnType<typeof useTestApiKeyMutation>;
export type TestApiKeyMutationResult = Apollo.MutationResult<TestApiKeyMutation>;
export type TestApiKeyMutationOptions = Apollo.BaseMutationOptions<TestApiKeyMutation, TestApiKeyMutationVariables>;
export const DeleteApiKeyDocument = gql`
    mutation DeleteApiKey($id: ApiKeyID!) {
  delete_api_key(id: $id) {
    success
    message
  }
}
    `;
export type DeleteApiKeyMutationFn = Apollo.MutationFunction<DeleteApiKeyMutation, DeleteApiKeyMutationVariables>;

/**
 * __useDeleteApiKeyMutation__
 *
 * To run a mutation, you first call `useDeleteApiKeyMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useDeleteApiKeyMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [deleteApiKeyMutation, { data, loading, error }] = useDeleteApiKeyMutation({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useDeleteApiKeyMutation(baseOptions?: Apollo.MutationHookOptions<DeleteApiKeyMutation, DeleteApiKeyMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<DeleteApiKeyMutation, DeleteApiKeyMutationVariables>(DeleteApiKeyDocument, options);
      }
export type DeleteApiKeyMutationHookResult = ReturnType<typeof useDeleteApiKeyMutation>;
export type DeleteApiKeyMutationResult = Apollo.MutationResult<DeleteApiKeyMutation>;
export type DeleteApiKeyMutationOptions = Apollo.BaseMutationOptions<DeleteApiKeyMutation, DeleteApiKeyMutationVariables>;
export const GetConversationsDocument = gql`
    query GetConversations($person_id: PersonID, $execution_id: ExecutionID, $search: String, $show_forgotten: Boolean = false, $limit: Int = 100, $offset: Int = 0, $since: DateTime) {
  conversations(
    person_id: $person_id
    execution_id: $execution_id
    search: $search
    show_forgotten: $show_forgotten
    limit: $limit
    offset: $offset
    since: $since
  )
}
    `;

/**
 * __useGetConversationsQuery__
 *
 * To run a query within a React component, call `useGetConversationsQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetConversationsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetConversationsQuery({
 *   variables: {
 *      person_id: // value for 'person_id'
 *      execution_id: // value for 'execution_id'
 *      search: // value for 'search'
 *      show_forgotten: // value for 'show_forgotten'
 *      limit: // value for 'limit'
 *      offset: // value for 'offset'
 *      since: // value for 'since'
 *   },
 * });
 */
export function useGetConversationsQuery(baseOptions?: Apollo.QueryHookOptions<GetConversationsQuery, GetConversationsQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetConversationsQuery, GetConversationsQueryVariables>(GetConversationsDocument, options);
      }
export function useGetConversationsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetConversationsQuery, GetConversationsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetConversationsQuery, GetConversationsQueryVariables>(GetConversationsDocument, options);
        }
export function useGetConversationsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetConversationsQuery, GetConversationsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetConversationsQuery, GetConversationsQueryVariables>(GetConversationsDocument, options);
        }
export type GetConversationsQueryHookResult = ReturnType<typeof useGetConversationsQuery>;
export type GetConversationsLazyQueryHookResult = ReturnType<typeof useGetConversationsLazyQuery>;
export type GetConversationsSuspenseQueryHookResult = ReturnType<typeof useGetConversationsSuspenseQuery>;
export type GetConversationsQueryResult = Apollo.QueryResult<GetConversationsQuery, GetConversationsQueryVariables>;
export const ClearConversationsDocument = gql`
    mutation ClearConversations {
  clear_conversations {
    success
    message
  }
}
    `;
export type ClearConversationsMutationFn = Apollo.MutationFunction<ClearConversationsMutation, ClearConversationsMutationVariables>;

/**
 * __useClearConversationsMutation__
 *
 * To run a mutation, you first call `useClearConversationsMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useClearConversationsMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [clearConversationsMutation, { data, loading, error }] = useClearConversationsMutation({
 *   variables: {
 *   },
 * });
 */
export function useClearConversationsMutation(baseOptions?: Apollo.MutationHookOptions<ClearConversationsMutation, ClearConversationsMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<ClearConversationsMutation, ClearConversationsMutationVariables>(ClearConversationsDocument, options);
      }
export type ClearConversationsMutationHookResult = ReturnType<typeof useClearConversationsMutation>;
export type ClearConversationsMutationResult = Apollo.MutationResult<ClearConversationsMutation>;
export type ClearConversationsMutationOptions = Apollo.BaseMutationOptions<ClearConversationsMutation, ClearConversationsMutationVariables>;
export const GetDiagramDocument = gql`
    query GetDiagram($id: DiagramID!) {
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

/**
 * __useGetDiagramQuery__
 *
 * To run a query within a React component, call `useGetDiagramQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetDiagramQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetDiagramQuery({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useGetDiagramQuery(baseOptions: Apollo.QueryHookOptions<GetDiagramQuery, GetDiagramQueryVariables> & ({ variables: GetDiagramQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetDiagramQuery, GetDiagramQueryVariables>(GetDiagramDocument, options);
      }
export function useGetDiagramLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetDiagramQuery, GetDiagramQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetDiagramQuery, GetDiagramQueryVariables>(GetDiagramDocument, options);
        }
export function useGetDiagramSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetDiagramQuery, GetDiagramQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetDiagramQuery, GetDiagramQueryVariables>(GetDiagramDocument, options);
        }
export type GetDiagramQueryHookResult = ReturnType<typeof useGetDiagramQuery>;
export type GetDiagramLazyQueryHookResult = ReturnType<typeof useGetDiagramLazyQuery>;
export type GetDiagramSuspenseQueryHookResult = ReturnType<typeof useGetDiagramSuspenseQuery>;
export type GetDiagramQueryResult = Apollo.QueryResult<GetDiagramQuery, GetDiagramQueryVariables>;
export const ListDiagramsDocument = gql`
    query ListDiagrams($filter: DiagramFilterInput, $limit: Int, $offset: Int) {
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

/**
 * __useListDiagramsQuery__
 *
 * To run a query within a React component, call `useListDiagramsQuery` and pass it any options that fit your needs.
 * When your component renders, `useListDiagramsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useListDiagramsQuery({
 *   variables: {
 *      filter: // value for 'filter'
 *      limit: // value for 'limit'
 *      offset: // value for 'offset'
 *   },
 * });
 */
export function useListDiagramsQuery(baseOptions?: Apollo.QueryHookOptions<ListDiagramsQuery, ListDiagramsQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ListDiagramsQuery, ListDiagramsQueryVariables>(ListDiagramsDocument, options);
      }
export function useListDiagramsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ListDiagramsQuery, ListDiagramsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ListDiagramsQuery, ListDiagramsQueryVariables>(ListDiagramsDocument, options);
        }
export function useListDiagramsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ListDiagramsQuery, ListDiagramsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ListDiagramsQuery, ListDiagramsQueryVariables>(ListDiagramsDocument, options);
        }
export type ListDiagramsQueryHookResult = ReturnType<typeof useListDiagramsQuery>;
export type ListDiagramsLazyQueryHookResult = ReturnType<typeof useListDiagramsLazyQuery>;
export type ListDiagramsSuspenseQueryHookResult = ReturnType<typeof useListDiagramsSuspenseQuery>;
export type ListDiagramsQueryResult = Apollo.QueryResult<ListDiagramsQuery, ListDiagramsQueryVariables>;
export const CreateDiagramDocument = gql`
    mutation CreateDiagram($input: CreateDiagramInput!) {
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
export type CreateDiagramMutationFn = Apollo.MutationFunction<CreateDiagramMutation, CreateDiagramMutationVariables>;

/**
 * __useCreateDiagramMutation__
 *
 * To run a mutation, you first call `useCreateDiagramMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useCreateDiagramMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [createDiagramMutation, { data, loading, error }] = useCreateDiagramMutation({
 *   variables: {
 *      input: // value for 'input'
 *   },
 * });
 */
export function useCreateDiagramMutation(baseOptions?: Apollo.MutationHookOptions<CreateDiagramMutation, CreateDiagramMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<CreateDiagramMutation, CreateDiagramMutationVariables>(CreateDiagramDocument, options);
      }
export type CreateDiagramMutationHookResult = ReturnType<typeof useCreateDiagramMutation>;
export type CreateDiagramMutationResult = Apollo.MutationResult<CreateDiagramMutation>;
export type CreateDiagramMutationOptions = Apollo.BaseMutationOptions<CreateDiagramMutation, CreateDiagramMutationVariables>;
export const ExecuteDiagramDocument = gql`
    mutation ExecuteDiagram($data: ExecuteDiagramInput!) {
  execute_diagram(data: $data) {
    success
    execution {
      id
    }
    message
    error
  }
}
    `;
export type ExecuteDiagramMutationFn = Apollo.MutationFunction<ExecuteDiagramMutation, ExecuteDiagramMutationVariables>;

/**
 * __useExecuteDiagramMutation__
 *
 * To run a mutation, you first call `useExecuteDiagramMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useExecuteDiagramMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [executeDiagramMutation, { data, loading, error }] = useExecuteDiagramMutation({
 *   variables: {
 *      data: // value for 'data'
 *   },
 * });
 */
export function useExecuteDiagramMutation(baseOptions?: Apollo.MutationHookOptions<ExecuteDiagramMutation, ExecuteDiagramMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<ExecuteDiagramMutation, ExecuteDiagramMutationVariables>(ExecuteDiagramDocument, options);
      }
export type ExecuteDiagramMutationHookResult = ReturnType<typeof useExecuteDiagramMutation>;
export type ExecuteDiagramMutationResult = Apollo.MutationResult<ExecuteDiagramMutation>;
export type ExecuteDiagramMutationOptions = Apollo.BaseMutationOptions<ExecuteDiagramMutation, ExecuteDiagramMutationVariables>;
export const DeleteDiagramDocument = gql`
    mutation DeleteDiagram($id: DiagramID!) {
  delete_diagram(id: $id) {
    success
    message
    error
  }
}
    `;
export type DeleteDiagramMutationFn = Apollo.MutationFunction<DeleteDiagramMutation, DeleteDiagramMutationVariables>;

/**
 * __useDeleteDiagramMutation__
 *
 * To run a mutation, you first call `useDeleteDiagramMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useDeleteDiagramMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [deleteDiagramMutation, { data, loading, error }] = useDeleteDiagramMutation({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useDeleteDiagramMutation(baseOptions?: Apollo.MutationHookOptions<DeleteDiagramMutation, DeleteDiagramMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<DeleteDiagramMutation, DeleteDiagramMutationVariables>(DeleteDiagramDocument, options);
      }
export type DeleteDiagramMutationHookResult = ReturnType<typeof useDeleteDiagramMutation>;
export type DeleteDiagramMutationResult = Apollo.MutationResult<DeleteDiagramMutation>;
export type DeleteDiagramMutationOptions = Apollo.BaseMutationOptions<DeleteDiagramMutation, DeleteDiagramMutationVariables>;
export const GetExecutionDocument = gql`
    query GetExecution($id: ExecutionID!) {
  execution(id: $id) {
    id
    status
    diagram_id
    started_at
    ended_at
    node_states
    node_outputs
    variables
    token_usage {
      input
      output
      cached
    }
    error
    duration_seconds
    is_active
  }
}
    `;

/**
 * __useGetExecutionQuery__
 *
 * To run a query within a React component, call `useGetExecutionQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetExecutionQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetExecutionQuery({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useGetExecutionQuery(baseOptions: Apollo.QueryHookOptions<GetExecutionQuery, GetExecutionQueryVariables> & ({ variables: GetExecutionQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetExecutionQuery, GetExecutionQueryVariables>(GetExecutionDocument, options);
      }
export function useGetExecutionLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetExecutionQuery, GetExecutionQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetExecutionQuery, GetExecutionQueryVariables>(GetExecutionDocument, options);
        }
export function useGetExecutionSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetExecutionQuery, GetExecutionQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetExecutionQuery, GetExecutionQueryVariables>(GetExecutionDocument, options);
        }
export type GetExecutionQueryHookResult = ReturnType<typeof useGetExecutionQuery>;
export type GetExecutionLazyQueryHookResult = ReturnType<typeof useGetExecutionLazyQuery>;
export type GetExecutionSuspenseQueryHookResult = ReturnType<typeof useGetExecutionSuspenseQuery>;
export type GetExecutionQueryResult = Apollo.QueryResult<GetExecutionQuery, GetExecutionQueryVariables>;
export const ListExecutionsDocument = gql`
    query ListExecutions($filter: ExecutionFilterInput, $limit: Int, $offset: Int) {
  executions(filter: $filter, limit: $limit, offset: $offset) {
    id
    status
    diagram_id
    started_at
    ended_at
    is_active
    duration_seconds
  }
}
    `;

/**
 * __useListExecutionsQuery__
 *
 * To run a query within a React component, call `useListExecutionsQuery` and pass it any options that fit your needs.
 * When your component renders, `useListExecutionsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useListExecutionsQuery({
 *   variables: {
 *      filter: // value for 'filter'
 *      limit: // value for 'limit'
 *      offset: // value for 'offset'
 *   },
 * });
 */
export function useListExecutionsQuery(baseOptions?: Apollo.QueryHookOptions<ListExecutionsQuery, ListExecutionsQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ListExecutionsQuery, ListExecutionsQueryVariables>(ListExecutionsDocument, options);
      }
export function useListExecutionsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ListExecutionsQuery, ListExecutionsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ListExecutionsQuery, ListExecutionsQueryVariables>(ListExecutionsDocument, options);
        }
export function useListExecutionsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ListExecutionsQuery, ListExecutionsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ListExecutionsQuery, ListExecutionsQueryVariables>(ListExecutionsDocument, options);
        }
export type ListExecutionsQueryHookResult = ReturnType<typeof useListExecutionsQuery>;
export type ListExecutionsLazyQueryHookResult = ReturnType<typeof useListExecutionsLazyQuery>;
export type ListExecutionsSuspenseQueryHookResult = ReturnType<typeof useListExecutionsSuspenseQuery>;
export type ListExecutionsQueryResult = Apollo.QueryResult<ListExecutionsQuery, ListExecutionsQueryVariables>;
export const ExecutionUpdatesDocument = gql`
    subscription ExecutionUpdates($executionId: ExecutionID!) {
  execution_updates(execution_id: $executionId) {
    id
    status
    node_states
    node_outputs
    token_usage {
      input
      output
      cached
    }
    error
  }
}
    `;

/**
 * __useExecutionUpdatesSubscription__
 *
 * To run a query within a React component, call `useExecutionUpdatesSubscription` and pass it any options that fit your needs.
 * When your component renders, `useExecutionUpdatesSubscription` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the subscription, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useExecutionUpdatesSubscription({
 *   variables: {
 *      executionId: // value for 'executionId'
 *   },
 * });
 */
export function useExecutionUpdatesSubscription(baseOptions: Apollo.SubscriptionHookOptions<ExecutionUpdatesSubscription, ExecutionUpdatesSubscriptionVariables> & ({ variables: ExecutionUpdatesSubscriptionVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useSubscription<ExecutionUpdatesSubscription, ExecutionUpdatesSubscriptionVariables>(ExecutionUpdatesDocument, options);
      }
export type ExecutionUpdatesSubscriptionHookResult = ReturnType<typeof useExecutionUpdatesSubscription>;
export type ExecutionUpdatesSubscriptionResult = Apollo.SubscriptionResult<ExecutionUpdatesSubscription>;
export const NodeUpdatesDocument = gql`
    subscription NodeUpdates($executionId: ExecutionID!, $nodeTypes: [NodeType!]) {
  node_updates(execution_id: $executionId, node_types: $nodeTypes) {
    execution_id
    node_id
    node_type
    status
    progress
    output
    error
    tokens_used
    timestamp
  }
}
    `;

/**
 * __useNodeUpdatesSubscription__
 *
 * To run a query within a React component, call `useNodeUpdatesSubscription` and pass it any options that fit your needs.
 * When your component renders, `useNodeUpdatesSubscription` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the subscription, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useNodeUpdatesSubscription({
 *   variables: {
 *      executionId: // value for 'executionId'
 *      nodeTypes: // value for 'nodeTypes'
 *   },
 * });
 */
export function useNodeUpdatesSubscription(baseOptions: Apollo.SubscriptionHookOptions<NodeUpdatesSubscription, NodeUpdatesSubscriptionVariables> & ({ variables: NodeUpdatesSubscriptionVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useSubscription<NodeUpdatesSubscription, NodeUpdatesSubscriptionVariables>(NodeUpdatesDocument, options);
      }
export type NodeUpdatesSubscriptionHookResult = ReturnType<typeof useNodeUpdatesSubscription>;
export type NodeUpdatesSubscriptionResult = Apollo.SubscriptionResult<NodeUpdatesSubscription>;
export const InteractivePromptsDocument = gql`
    subscription InteractivePrompts($executionId: ExecutionID!) {
  interactive_prompts(execution_id: $executionId) {
    execution_id
    node_id
    prompt
    timeout_seconds
    timestamp
  }
}
    `;

/**
 * __useInteractivePromptsSubscription__
 *
 * To run a query within a React component, call `useInteractivePromptsSubscription` and pass it any options that fit your needs.
 * When your component renders, `useInteractivePromptsSubscription` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the subscription, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useInteractivePromptsSubscription({
 *   variables: {
 *      executionId: // value for 'executionId'
 *   },
 * });
 */
export function useInteractivePromptsSubscription(baseOptions: Apollo.SubscriptionHookOptions<InteractivePromptsSubscription, InteractivePromptsSubscriptionVariables> & ({ variables: InteractivePromptsSubscriptionVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useSubscription<InteractivePromptsSubscription, InteractivePromptsSubscriptionVariables>(InteractivePromptsDocument, options);
      }
export type InteractivePromptsSubscriptionHookResult = ReturnType<typeof useInteractivePromptsSubscription>;
export type InteractivePromptsSubscriptionResult = Apollo.SubscriptionResult<InteractivePromptsSubscription>;
export const ControlExecutionDocument = gql`
    mutation ControlExecution($data: ExecutionControlInput!) {
  control_execution(data: $data) {
    success
    execution {
      id
      status
    }
    message
    error
  }
}
    `;
export type ControlExecutionMutationFn = Apollo.MutationFunction<ControlExecutionMutation, ControlExecutionMutationVariables>;

/**
 * __useControlExecutionMutation__
 *
 * To run a mutation, you first call `useControlExecutionMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useControlExecutionMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [controlExecutionMutation, { data, loading, error }] = useControlExecutionMutation({
 *   variables: {
 *      data: // value for 'data'
 *   },
 * });
 */
export function useControlExecutionMutation(baseOptions?: Apollo.MutationHookOptions<ControlExecutionMutation, ControlExecutionMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<ControlExecutionMutation, ControlExecutionMutationVariables>(ControlExecutionDocument, options);
      }
export type ControlExecutionMutationHookResult = ReturnType<typeof useControlExecutionMutation>;
export type ControlExecutionMutationResult = Apollo.MutationResult<ControlExecutionMutation>;
export type ControlExecutionMutationOptions = Apollo.BaseMutationOptions<ControlExecutionMutation, ControlExecutionMutationVariables>;
export const SubmitInteractiveResponseDocument = gql`
    mutation SubmitInteractiveResponse($data: InteractiveResponseInput!) {
  submit_interactive_response(data: $data) {
    success
    execution {
      id
      status
      node_states
    }
    message
    error
  }
}
    `;
export type SubmitInteractiveResponseMutationFn = Apollo.MutationFunction<SubmitInteractiveResponseMutation, SubmitInteractiveResponseMutationVariables>;

/**
 * __useSubmitInteractiveResponseMutation__
 *
 * To run a mutation, you first call `useSubmitInteractiveResponseMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useSubmitInteractiveResponseMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [submitInteractiveResponseMutation, { data, loading, error }] = useSubmitInteractiveResponseMutation({
 *   variables: {
 *      data: // value for 'data'
 *   },
 * });
 */
export function useSubmitInteractiveResponseMutation(baseOptions?: Apollo.MutationHookOptions<SubmitInteractiveResponseMutation, SubmitInteractiveResponseMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<SubmitInteractiveResponseMutation, SubmitInteractiveResponseMutationVariables>(SubmitInteractiveResponseDocument, options);
      }
export type SubmitInteractiveResponseMutationHookResult = ReturnType<typeof useSubmitInteractiveResponseMutation>;
export type SubmitInteractiveResponseMutationResult = Apollo.MutationResult<SubmitInteractiveResponseMutation>;
export type SubmitInteractiveResponseMutationOptions = Apollo.BaseMutationOptions<SubmitInteractiveResponseMutation, SubmitInteractiveResponseMutationVariables>;
export const UploadFileDocument = gql`
    mutation UploadFile($file: Upload!, $category: String! = "general") {
  upload_file(file: $file, category: $category) {
    success
    path
    size_bytes
    content_type
    message
    error
  }
}
    `;
export type UploadFileMutationFn = Apollo.MutationFunction<UploadFileMutation, UploadFileMutationVariables>;

/**
 * __useUploadFileMutation__
 *
 * To run a mutation, you first call `useUploadFileMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useUploadFileMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [uploadFileMutation, { data, loading, error }] = useUploadFileMutation({
 *   variables: {
 *      file: // value for 'file'
 *      category: // value for 'category'
 *   },
 * });
 */
export function useUploadFileMutation(baseOptions?: Apollo.MutationHookOptions<UploadFileMutation, UploadFileMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<UploadFileMutation, UploadFileMutationVariables>(UploadFileDocument, options);
      }
export type UploadFileMutationHookResult = ReturnType<typeof useUploadFileMutation>;
export type UploadFileMutationResult = Apollo.MutationResult<UploadFileMutation>;
export type UploadFileMutationOptions = Apollo.BaseMutationOptions<UploadFileMutation, UploadFileMutationVariables>;
export const ValidateDiagramDocument = gql`
    mutation ValidateDiagram($diagramContent: JSONScalar!) {
  validate_diagram(diagram_content: $diagramContent) {
    is_valid
    errors
    node_count
    arrow_count
    person_count
  }
}
    `;
export type ValidateDiagramMutationFn = Apollo.MutationFunction<ValidateDiagramMutation, ValidateDiagramMutationVariables>;

/**
 * __useValidateDiagramMutation__
 *
 * To run a mutation, you first call `useValidateDiagramMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useValidateDiagramMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [validateDiagramMutation, { data, loading, error }] = useValidateDiagramMutation({
 *   variables: {
 *      diagramContent: // value for 'diagramContent'
 *   },
 * });
 */
export function useValidateDiagramMutation(baseOptions?: Apollo.MutationHookOptions<ValidateDiagramMutation, ValidateDiagramMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<ValidateDiagramMutation, ValidateDiagramMutationVariables>(ValidateDiagramDocument, options);
      }
export type ValidateDiagramMutationHookResult = ReturnType<typeof useValidateDiagramMutation>;
export type ValidateDiagramMutationResult = Apollo.MutationResult<ValidateDiagramMutation>;
export type ValidateDiagramMutationOptions = Apollo.BaseMutationOptions<ValidateDiagramMutation, ValidateDiagramMutationVariables>;
export const ConvertDiagramDocument = gql`
    mutation ConvertDiagram($content: JSONScalar!, $targetFormat: DiagramFormat = NATIVE, $includeMetadata: Boolean = true) {
  convert_diagram(
    content: $content
    target_format: $targetFormat
    include_metadata: $includeMetadata
  ) {
    success
    message
    error
    content
    format
    filename
  }
}
    `;
export type ConvertDiagramMutationFn = Apollo.MutationFunction<ConvertDiagramMutation, ConvertDiagramMutationVariables>;

/**
 * __useConvertDiagramMutation__
 *
 * To run a mutation, you first call `useConvertDiagramMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useConvertDiagramMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [convertDiagramMutation, { data, loading, error }] = useConvertDiagramMutation({
 *   variables: {
 *      content: // value for 'content'
 *      targetFormat: // value for 'targetFormat'
 *      includeMetadata: // value for 'includeMetadata'
 *   },
 * });
 */
export function useConvertDiagramMutation(baseOptions?: Apollo.MutationHookOptions<ConvertDiagramMutation, ConvertDiagramMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<ConvertDiagramMutation, ConvertDiagramMutationVariables>(ConvertDiagramDocument, options);
      }
export type ConvertDiagramMutationHookResult = ReturnType<typeof useConvertDiagramMutation>;
export type ConvertDiagramMutationResult = Apollo.MutationResult<ConvertDiagramMutation>;
export type ConvertDiagramMutationOptions = Apollo.BaseMutationOptions<ConvertDiagramMutation, ConvertDiagramMutationVariables>;
export const GetSupportedFormatsDocument = gql`
    query GetSupportedFormats {
  supported_formats {
    format
    name
    extension
    supports_export
    supports_import
    description
  }
}
    `;

/**
 * __useGetSupportedFormatsQuery__
 *
 * To run a query within a React component, call `useGetSupportedFormatsQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetSupportedFormatsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetSupportedFormatsQuery({
 *   variables: {
 *   },
 * });
 */
export function useGetSupportedFormatsQuery(baseOptions?: Apollo.QueryHookOptions<GetSupportedFormatsQuery, GetSupportedFormatsQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetSupportedFormatsQuery, GetSupportedFormatsQueryVariables>(GetSupportedFormatsDocument, options);
      }
export function useGetSupportedFormatsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetSupportedFormatsQuery, GetSupportedFormatsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetSupportedFormatsQuery, GetSupportedFormatsQueryVariables>(GetSupportedFormatsDocument, options);
        }
export function useGetSupportedFormatsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetSupportedFormatsQuery, GetSupportedFormatsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetSupportedFormatsQuery, GetSupportedFormatsQueryVariables>(GetSupportedFormatsDocument, options);
        }
export type GetSupportedFormatsQueryHookResult = ReturnType<typeof useGetSupportedFormatsQuery>;
export type GetSupportedFormatsLazyQueryHookResult = ReturnType<typeof useGetSupportedFormatsLazyQuery>;
export type GetSupportedFormatsSuspenseQueryHookResult = ReturnType<typeof useGetSupportedFormatsSuspenseQuery>;
export type GetSupportedFormatsQueryResult = Apollo.QueryResult<GetSupportedFormatsQuery, GetSupportedFormatsQueryVariables>;
export const CreateNodeDocument = gql`
    mutation CreateNode($diagramId: DiagramID!, $inputData: CreateNodeInput!) {
  create_node(diagram_id: $diagramId, input_data: $inputData) {
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
export type CreateNodeMutationFn = Apollo.MutationFunction<CreateNodeMutation, CreateNodeMutationVariables>;

/**
 * __useCreateNodeMutation__
 *
 * To run a mutation, you first call `useCreateNodeMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useCreateNodeMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [createNodeMutation, { data, loading, error }] = useCreateNodeMutation({
 *   variables: {
 *      diagramId: // value for 'diagramId'
 *      inputData: // value for 'inputData'
 *   },
 * });
 */
export function useCreateNodeMutation(baseOptions?: Apollo.MutationHookOptions<CreateNodeMutation, CreateNodeMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<CreateNodeMutation, CreateNodeMutationVariables>(CreateNodeDocument, options);
      }
export type CreateNodeMutationHookResult = ReturnType<typeof useCreateNodeMutation>;
export type CreateNodeMutationResult = Apollo.MutationResult<CreateNodeMutation>;
export type CreateNodeMutationOptions = Apollo.BaseMutationOptions<CreateNodeMutation, CreateNodeMutationVariables>;
export const UpdateNodeDocument = gql`
    mutation UpdateNode($inputData: UpdateNodeInput!) {
  update_node(input_data: $inputData) {
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
export type UpdateNodeMutationFn = Apollo.MutationFunction<UpdateNodeMutation, UpdateNodeMutationVariables>;

/**
 * __useUpdateNodeMutation__
 *
 * To run a mutation, you first call `useUpdateNodeMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useUpdateNodeMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [updateNodeMutation, { data, loading, error }] = useUpdateNodeMutation({
 *   variables: {
 *      inputData: // value for 'inputData'
 *   },
 * });
 */
export function useUpdateNodeMutation(baseOptions?: Apollo.MutationHookOptions<UpdateNodeMutation, UpdateNodeMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<UpdateNodeMutation, UpdateNodeMutationVariables>(UpdateNodeDocument, options);
      }
export type UpdateNodeMutationHookResult = ReturnType<typeof useUpdateNodeMutation>;
export type UpdateNodeMutationResult = Apollo.MutationResult<UpdateNodeMutation>;
export type UpdateNodeMutationOptions = Apollo.BaseMutationOptions<UpdateNodeMutation, UpdateNodeMutationVariables>;
export const DeleteNodeDocument = gql`
    mutation DeleteNode($nodeId: NodeID!) {
  delete_node(node_id: $nodeId) {
    success
    message
    error
  }
}
    `;
export type DeleteNodeMutationFn = Apollo.MutationFunction<DeleteNodeMutation, DeleteNodeMutationVariables>;

/**
 * __useDeleteNodeMutation__
 *
 * To run a mutation, you first call `useDeleteNodeMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useDeleteNodeMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [deleteNodeMutation, { data, loading, error }] = useDeleteNodeMutation({
 *   variables: {
 *      nodeId: // value for 'nodeId'
 *   },
 * });
 */
export function useDeleteNodeMutation(baseOptions?: Apollo.MutationHookOptions<DeleteNodeMutation, DeleteNodeMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<DeleteNodeMutation, DeleteNodeMutationVariables>(DeleteNodeDocument, options);
      }
export type DeleteNodeMutationHookResult = ReturnType<typeof useDeleteNodeMutation>;
export type DeleteNodeMutationResult = Apollo.MutationResult<DeleteNodeMutation>;
export type DeleteNodeMutationOptions = Apollo.BaseMutationOptions<DeleteNodeMutation, DeleteNodeMutationVariables>;
export const GetPersonDocument = gql`
    query GetPerson($id: PersonID!) {
  person(id: $id) {
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
}
    `;

/**
 * __useGetPersonQuery__
 *
 * To run a query within a React component, call `useGetPersonQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetPersonQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetPersonQuery({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useGetPersonQuery(baseOptions: Apollo.QueryHookOptions<GetPersonQuery, GetPersonQueryVariables> & ({ variables: GetPersonQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetPersonQuery, GetPersonQueryVariables>(GetPersonDocument, options);
      }
export function useGetPersonLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetPersonQuery, GetPersonQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetPersonQuery, GetPersonQueryVariables>(GetPersonDocument, options);
        }
export function useGetPersonSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetPersonQuery, GetPersonQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetPersonQuery, GetPersonQueryVariables>(GetPersonDocument, options);
        }
export type GetPersonQueryHookResult = ReturnType<typeof useGetPersonQuery>;
export type GetPersonLazyQueryHookResult = ReturnType<typeof useGetPersonLazyQuery>;
export type GetPersonSuspenseQueryHookResult = ReturnType<typeof useGetPersonSuspenseQuery>;
export type GetPersonQueryResult = Apollo.QueryResult<GetPersonQuery, GetPersonQueryVariables>;
export const GetPersonsDocument = gql`
    query GetPersons($limit: Int = 100) {
  persons(limit: $limit) {
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
}
    `;

/**
 * __useGetPersonsQuery__
 *
 * To run a query within a React component, call `useGetPersonsQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetPersonsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetPersonsQuery({
 *   variables: {
 *      limit: // value for 'limit'
 *   },
 * });
 */
export function useGetPersonsQuery(baseOptions?: Apollo.QueryHookOptions<GetPersonsQuery, GetPersonsQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetPersonsQuery, GetPersonsQueryVariables>(GetPersonsDocument, options);
      }
export function useGetPersonsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetPersonsQuery, GetPersonsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetPersonsQuery, GetPersonsQueryVariables>(GetPersonsDocument, options);
        }
export function useGetPersonsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetPersonsQuery, GetPersonsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetPersonsQuery, GetPersonsQueryVariables>(GetPersonsDocument, options);
        }
export type GetPersonsQueryHookResult = ReturnType<typeof useGetPersonsQuery>;
export type GetPersonsLazyQueryHookResult = ReturnType<typeof useGetPersonsLazyQuery>;
export type GetPersonsSuspenseQueryHookResult = ReturnType<typeof useGetPersonsSuspenseQuery>;
export type GetPersonsQueryResult = Apollo.QueryResult<GetPersonsQuery, GetPersonsQueryVariables>;
export const CreatePersonDocument = gql`
    mutation CreatePerson($diagramId: DiagramID!, $personInput: CreatePersonInput!) {
  create_person(diagram_id: $diagramId, person_input: $personInput) {
    success
    person {
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
    message
    error
  }
}
    `;
export type CreatePersonMutationFn = Apollo.MutationFunction<CreatePersonMutation, CreatePersonMutationVariables>;

/**
 * __useCreatePersonMutation__
 *
 * To run a mutation, you first call `useCreatePersonMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useCreatePersonMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [createPersonMutation, { data, loading, error }] = useCreatePersonMutation({
 *   variables: {
 *      diagramId: // value for 'diagramId'
 *      personInput: // value for 'personInput'
 *   },
 * });
 */
export function useCreatePersonMutation(baseOptions?: Apollo.MutationHookOptions<CreatePersonMutation, CreatePersonMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<CreatePersonMutation, CreatePersonMutationVariables>(CreatePersonDocument, options);
      }
export type CreatePersonMutationHookResult = ReturnType<typeof useCreatePersonMutation>;
export type CreatePersonMutationResult = Apollo.MutationResult<CreatePersonMutation>;
export type CreatePersonMutationOptions = Apollo.BaseMutationOptions<CreatePersonMutation, CreatePersonMutationVariables>;
export const UpdatePersonDocument = gql`
    mutation UpdatePerson($personInput: UpdatePersonInput!) {
  update_person(person_input: $personInput) {
    success
    person {
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
    message
    error
  }
}
    `;
export type UpdatePersonMutationFn = Apollo.MutationFunction<UpdatePersonMutation, UpdatePersonMutationVariables>;

/**
 * __useUpdatePersonMutation__
 *
 * To run a mutation, you first call `useUpdatePersonMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useUpdatePersonMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [updatePersonMutation, { data, loading, error }] = useUpdatePersonMutation({
 *   variables: {
 *      personInput: // value for 'personInput'
 *   },
 * });
 */
export function useUpdatePersonMutation(baseOptions?: Apollo.MutationHookOptions<UpdatePersonMutation, UpdatePersonMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<UpdatePersonMutation, UpdatePersonMutationVariables>(UpdatePersonDocument, options);
      }
export type UpdatePersonMutationHookResult = ReturnType<typeof useUpdatePersonMutation>;
export type UpdatePersonMutationResult = Apollo.MutationResult<UpdatePersonMutation>;
export type UpdatePersonMutationOptions = Apollo.BaseMutationOptions<UpdatePersonMutation, UpdatePersonMutationVariables>;
export const DeletePersonDocument = gql`
    mutation DeletePerson($personId: PersonID!) {
  delete_person(person_id: $personId) {
    success
    message
    error
  }
}
    `;
export type DeletePersonMutationFn = Apollo.MutationFunction<DeletePersonMutation, DeletePersonMutationVariables>;

/**
 * __useDeletePersonMutation__
 *
 * To run a mutation, you first call `useDeletePersonMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useDeletePersonMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [deletePersonMutation, { data, loading, error }] = useDeletePersonMutation({
 *   variables: {
 *      personId: // value for 'personId'
 *   },
 * });
 */
export function useDeletePersonMutation(baseOptions?: Apollo.MutationHookOptions<DeletePersonMutation, DeletePersonMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<DeletePersonMutation, DeletePersonMutationVariables>(DeletePersonDocument, options);
      }
export type DeletePersonMutationHookResult = ReturnType<typeof useDeletePersonMutation>;
export type DeletePersonMutationResult = Apollo.MutationResult<DeletePersonMutation>;
export type DeletePersonMutationOptions = Apollo.BaseMutationOptions<DeletePersonMutation, DeletePersonMutationVariables>;
export const InitializeModelDocument = gql`
    mutation InitializeModel($personId: PersonID!, $apiKeyId: ApiKeyID!, $model: String!, $label: String!) {
  initialize_model(
    person_id: $personId
    api_key_id: $apiKeyId
    model: $model
    label: $label
  ) {
    success
    person {
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
    message
    error
  }
}
    `;
export type InitializeModelMutationFn = Apollo.MutationFunction<InitializeModelMutation, InitializeModelMutationVariables>;

/**
 * __useInitializeModelMutation__
 *
 * To run a mutation, you first call `useInitializeModelMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useInitializeModelMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [initializeModelMutation, { data, loading, error }] = useInitializeModelMutation({
 *   variables: {
 *      personId: // value for 'personId'
 *      apiKeyId: // value for 'apiKeyId'
 *      model: // value for 'model'
 *      label: // value for 'label'
 *   },
 * });
 */
export function useInitializeModelMutation(baseOptions?: Apollo.MutationHookOptions<InitializeModelMutation, InitializeModelMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<InitializeModelMutation, InitializeModelMutationVariables>(InitializeModelDocument, options);
      }
export type InitializeModelMutationHookResult = ReturnType<typeof useInitializeModelMutation>;
export type InitializeModelMutationResult = Apollo.MutationResult<InitializeModelMutation>;
export type InitializeModelMutationOptions = Apollo.BaseMutationOptions<InitializeModelMutation, InitializeModelMutationVariables>;
export const GetPromptFilesDocument = gql`
    query GetPromptFiles {
  prompt_files
}
    `;

/**
 * __useGetPromptFilesQuery__
 *
 * To run a query within a React component, call `useGetPromptFilesQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetPromptFilesQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetPromptFilesQuery({
 *   variables: {
 *   },
 * });
 */
export function useGetPromptFilesQuery(baseOptions?: Apollo.QueryHookOptions<GetPromptFilesQuery, GetPromptFilesQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetPromptFilesQuery, GetPromptFilesQueryVariables>(GetPromptFilesDocument, options);
      }
export function useGetPromptFilesLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetPromptFilesQuery, GetPromptFilesQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetPromptFilesQuery, GetPromptFilesQueryVariables>(GetPromptFilesDocument, options);
        }
export function useGetPromptFilesSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetPromptFilesQuery, GetPromptFilesQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetPromptFilesQuery, GetPromptFilesQueryVariables>(GetPromptFilesDocument, options);
        }
export type GetPromptFilesQueryHookResult = ReturnType<typeof useGetPromptFilesQuery>;
export type GetPromptFilesLazyQueryHookResult = ReturnType<typeof useGetPromptFilesLazyQuery>;
export type GetPromptFilesSuspenseQueryHookResult = ReturnType<typeof useGetPromptFilesSuspenseQuery>;
export type GetPromptFilesQueryResult = Apollo.QueryResult<GetPromptFilesQuery, GetPromptFilesQueryVariables>;
export const GetPromptFileDocument = gql`
    query GetPromptFile($filename: String!) {
  prompt_file(filename: $filename)
}
    `;

/**
 * __useGetPromptFileQuery__
 *
 * To run a query within a React component, call `useGetPromptFileQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetPromptFileQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetPromptFileQuery({
 *   variables: {
 *      filename: // value for 'filename'
 *   },
 * });
 */
export function useGetPromptFileQuery(baseOptions: Apollo.QueryHookOptions<GetPromptFileQuery, GetPromptFileQueryVariables> & ({ variables: GetPromptFileQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetPromptFileQuery, GetPromptFileQueryVariables>(GetPromptFileDocument, options);
      }
export function useGetPromptFileLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetPromptFileQuery, GetPromptFileQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetPromptFileQuery, GetPromptFileQueryVariables>(GetPromptFileDocument, options);
        }
export function useGetPromptFileSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetPromptFileQuery, GetPromptFileQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetPromptFileQuery, GetPromptFileQueryVariables>(GetPromptFileDocument, options);
        }
export type GetPromptFileQueryHookResult = ReturnType<typeof useGetPromptFileQuery>;
export type GetPromptFileLazyQueryHookResult = ReturnType<typeof useGetPromptFileLazyQuery>;
export type GetPromptFileSuspenseQueryHookResult = ReturnType<typeof useGetPromptFileSuspenseQuery>;
export type GetPromptFileQueryResult = Apollo.QueryResult<GetPromptFileQuery, GetPromptFileQueryVariables>;
export const GetSystemInfoDocument = gql`
    query GetSystemInfo {
  system_info
}
    `;

/**
 * __useGetSystemInfoQuery__
 *
 * To run a query within a React component, call `useGetSystemInfoQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetSystemInfoQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetSystemInfoQuery({
 *   variables: {
 *   },
 * });
 */
export function useGetSystemInfoQuery(baseOptions?: Apollo.QueryHookOptions<GetSystemInfoQuery, GetSystemInfoQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetSystemInfoQuery, GetSystemInfoQueryVariables>(GetSystemInfoDocument, options);
      }
export function useGetSystemInfoLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetSystemInfoQuery, GetSystemInfoQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetSystemInfoQuery, GetSystemInfoQueryVariables>(GetSystemInfoDocument, options);
        }
export function useGetSystemInfoSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetSystemInfoQuery, GetSystemInfoQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetSystemInfoQuery, GetSystemInfoQueryVariables>(GetSystemInfoDocument, options);
        }
export type GetSystemInfoQueryHookResult = ReturnType<typeof useGetSystemInfoQuery>;
export type GetSystemInfoLazyQueryHookResult = ReturnType<typeof useGetSystemInfoLazyQuery>;
export type GetSystemInfoSuspenseQueryHookResult = ReturnType<typeof useGetSystemInfoSuspenseQuery>;
export type GetSystemInfoQueryResult = Apollo.QueryResult<GetSystemInfoQuery, GetSystemInfoQueryVariables>;
export const ExecutionOrderDocument = gql`
    query ExecutionOrder($executionId: ExecutionID!) {
  execution_order(execution_id: $executionId)
}
    `;

/**
 * __useExecutionOrderQuery__
 *
 * To run a query within a React component, call `useExecutionOrderQuery` and pass it any options that fit your needs.
 * When your component renders, `useExecutionOrderQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useExecutionOrderQuery({
 *   variables: {
 *      executionId: // value for 'executionId'
 *   },
 * });
 */
export function useExecutionOrderQuery(baseOptions: Apollo.QueryHookOptions<ExecutionOrderQuery, ExecutionOrderQueryVariables> & ({ variables: ExecutionOrderQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ExecutionOrderQuery, ExecutionOrderQueryVariables>(ExecutionOrderDocument, options);
      }
export function useExecutionOrderLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ExecutionOrderQuery, ExecutionOrderQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ExecutionOrderQuery, ExecutionOrderQueryVariables>(ExecutionOrderDocument, options);
        }
export function useExecutionOrderSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ExecutionOrderQuery, ExecutionOrderQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ExecutionOrderQuery, ExecutionOrderQueryVariables>(ExecutionOrderDocument, options);
        }
export type ExecutionOrderQueryHookResult = ReturnType<typeof useExecutionOrderQuery>;
export type ExecutionOrderLazyQueryHookResult = ReturnType<typeof useExecutionOrderLazyQuery>;
export type ExecutionOrderSuspenseQueryHookResult = ReturnType<typeof useExecutionOrderSuspenseQuery>;
export type ExecutionOrderQueryResult = Apollo.QueryResult<ExecutionOrderQuery, ExecutionOrderQueryVariables>;