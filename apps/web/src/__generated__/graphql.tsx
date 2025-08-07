import type { NodeType } from '@dipeo/models';
import type { HandleDirection } from '@dipeo/models';
import type { HandleLabel } from '@dipeo/models';
import type { DataType } from '@dipeo/models';
import type { LLMService } from '@dipeo/models';
import type { DiagramFormat } from '@dipeo/models';
import type { Status } from '@dipeo/models';
import type { ApiKeyID } from '@dipeo/models';
import type { ArrowID } from '@dipeo/models';
import type { DiagramID } from '@dipeo/models';
import type { ExecutionID } from '@dipeo/models';
import type { HandleID } from '@dipeo/models';
import type { NodeID } from '@dipeo/models';
import type { PersonID } from '@dipeo/models';
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
  /** Unique identifier for API keys */
  ApiKeyID: { input: ApiKeyID; output: ApiKeyID; }
  /** Unique identifier for arrows */
  ArrowID: { input: ArrowID; output: ArrowID; }
  /** Date with time (isoformat) */
  DateTime: { input: any; output: any; }
  /** Unique identifier for diagrams */
  DiagramID: { input: DiagramID; output: DiagramID; }
  /** Unique identifier for executions */
  ExecutionID: { input: ExecutionID; output: ExecutionID; }
  /** Unique identifier for handles */
  HandleID: { input: HandleID; output: HandleID; }
  /** Unique identifier for hooks */
  HookID: { input: any; output: any; }
  /** The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf). */
  JSON: { input: any; output: any; }
  /** Unique identifier for nodes */
  NodeID: { input: NodeID; output: NodeID; }
  /** Unique identifier for persons */
  PersonID: { input: PersonID; output: PersonID; }
  /** Unique identifier for tasks */
  TaskID: { input: any; output: any; }
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
  OLLAMA = 'OLLAMA',
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

export type CliSession = {
  __typename?: 'CliSession';
  diagram_data?: Maybe<Scalars['String']['output']>;
  diagram_format: Scalars['String']['output'];
  diagram_name: Scalars['String']['output'];
  execution_id: Scalars['String']['output'];
  is_active: Scalars['Boolean']['output'];
  session_id: Scalars['String']['output'];
  started_at: Scalars['DateTime']['output'];
};

export type CliSessionResult = {
  __typename?: 'CliSessionResult';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export enum ContentType {
  CONVERSATION_STATE = 'CONVERSATION_STATE',
  EMPTY = 'EMPTY',
  GENERIC = 'GENERIC',
  OBJECT = 'OBJECT',
  RAW_TEXT = 'RAW_TEXT',
  VARIABLE = 'VARIABLE'
}

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
  data: Scalars['JSON']['input'];
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
  deleted_id?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type DiagramConvertResult = {
  __typename?: 'DiagramConvertResult';
  content?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  format?: Maybe<DiagramFormat>;
  message?: Maybe<Scalars['String']['output']>;
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
  format?: Maybe<Scalars['String']['output']>;
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
  errors?: Maybe<Array<Scalars['String']['output']>>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
  warnings?: Maybe<Array<Scalars['String']['output']>>;
};

export type DomainApiKeyType = {
  __typename?: 'DomainApiKeyType';
  id: Scalars['String']['output'];
  key?: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  service: APIServiceType;
};

export type DomainArrowType = {
  __typename?: 'DomainArrowType';
  content_type?: Maybe<ContentType>;
  data?: Maybe<Scalars['JSON']['output']>;
  id: Scalars['String']['output'];
  label?: Maybe<Scalars['String']['output']>;
  source: Scalars['String']['output'];
  target: Scalars['String']['output'];
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
  id: Scalars['String']['output'];
  label: HandleLabel;
  node_id: Scalars['String']['output'];
  position?: Maybe<Scalars['String']['output']>;
};

export type DomainNodeType = {
  __typename?: 'DomainNodeType';
  data: Scalars['JSON']['output'];
  id: Scalars['String']['output'];
  position: Vec2Type;
  type: NodeType;
};

export type DomainPersonType = {
  __typename?: 'DomainPersonType';
  id: Scalars['String']['output'];
  label: Scalars['String']['output'];
  llm_config: PersonLLMConfigType;
  type: Scalars['String']['output'];
};

export type ExecuteDiagramInput = {
  debug_mode?: InputMaybe<Scalars['Boolean']['input']>;
  diagram_data?: InputMaybe<Scalars['JSON']['input']>;
  diagram_id?: InputMaybe<Scalars['ID']['input']>;
  max_iterations?: InputMaybe<Scalars['Int']['input']>;
  timeout_seconds?: InputMaybe<Scalars['Int']['input']>;
  use_unified_monitoring?: InputMaybe<Scalars['Boolean']['input']>;
  variables?: InputMaybe<Scalars['JSON']['input']>;
};

export type ExecutionControlInput = {
  action: Scalars['String']['input'];
  execution_id: Scalars['ID']['input'];
  reason?: InputMaybe<Scalars['String']['input']>;
};

export type ExecutionFilterInput = {
  diagram_id?: InputMaybe<Scalars['ID']['input']>;
  started_after?: InputMaybe<Scalars['DateTime']['input']>;
  started_before?: InputMaybe<Scalars['DateTime']['input']>;
  status?: InputMaybe<Status>;
};

export type ExecutionResult = {
  __typename?: 'ExecutionResult';
  error?: Maybe<Scalars['String']['output']>;
  execution?: Maybe<ExecutionStateType>;
  execution_id?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type ExecutionStateType = {
  __typename?: 'ExecutionStateType';
  diagram_id?: Maybe<Scalars['String']['output']>;
  duration_seconds?: Maybe<Scalars['Float']['output']>;
  ended_at?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  exec_counts: Scalars['JSON']['output'];
  executed_nodes: Array<Scalars['String']['output']>;
  id: Scalars['String']['output'];
  is_active?: Maybe<Scalars['Boolean']['output']>;
  metrics?: Maybe<Scalars['JSON']['output']>;
  node_outputs: Scalars['JSON']['output'];
  node_states: Scalars['JSON']['output'];
  started_at: Scalars['String']['output'];
  status: Status;
  token_usage: TokenUsageType;
  variables?: Maybe<Scalars['JSON']['output']>;
};

export type ExecutionUpdate = {
  __typename?: 'ExecutionUpdate';
  data: Scalars['JSON']['output'];
  event_type: Scalars['String']['output'];
  execution_id: Scalars['String']['output'];
  timestamp: Scalars['String']['output'];
};

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

export type InteractiveResponseInput = {
  execution_id: Scalars['ID']['input'];
  metadata?: InputMaybe<Scalars['JSON']['input']>;
  node_id: Scalars['ID']['input'];
  response: Scalars['String']['input'];
};

export { LLMService };

export type Mutation = {
  __typename?: 'Mutation';
  control_execution: ExecutionResult;
  convert_diagram_format: DiagramConvertResult;
  create_api_key: ApiKeyResult;
  create_diagram: DiagramResult;
  create_node: NodeResult;
  create_person: PersonResult;
  delete_api_key: DeleteResult;
  delete_diagram: DeleteResult;
  delete_node: DeleteResult;
  delete_person: DeleteResult;
  execute_diagram: ExecutionResult;
  register_cli_session: CliSessionResult;
  send_interactive_response: ExecutionResult;
  test_api_key: TestApiKeyResult;
  unregister_cli_session: CliSessionResult;
  update_node: NodeResult;
  update_node_state: ExecutionResult;
  update_person: PersonResult;
  upload_diagram: DiagramResult;
  upload_file: FileUploadResult;
  validate_diagram: DiagramValidationResult;
};


export type Mutationcontrol_executionArgs = {
  input: ExecutionControlInput;
};


export type Mutationconvert_diagram_formatArgs = {
  content: Scalars['String']['input'];
  from_format: DiagramFormat;
  to_format: DiagramFormat;
};


export type Mutationcreate_api_keyArgs = {
  input: CreateApiKeyInput;
};


export type Mutationcreate_diagramArgs = {
  input: CreateDiagramInput;
};


export type Mutationcreate_nodeArgs = {
  diagram_id: Scalars['ID']['input'];
  input: CreateNodeInput;
};


export type Mutationcreate_personArgs = {
  input: CreatePersonInput;
};


export type Mutationdelete_api_keyArgs = {
  id: Scalars['ID']['input'];
};


export type Mutationdelete_diagramArgs = {
  id: Scalars['ID']['input'];
};


export type Mutationdelete_nodeArgs = {
  diagram_id: Scalars['ID']['input'];
  node_id: Scalars['ID']['input'];
};


export type Mutationdelete_personArgs = {
  id: Scalars['ID']['input'];
};


export type Mutationexecute_diagramArgs = {
  input: ExecuteDiagramInput;
};


export type Mutationregister_cli_sessionArgs = {
  input: RegisterCliSessionInput;
};


export type Mutationsend_interactive_responseArgs = {
  input: InteractiveResponseInput;
};


export type Mutationtest_api_keyArgs = {
  id: Scalars['ID']['input'];
};


export type Mutationunregister_cli_sessionArgs = {
  input: UnregisterCliSessionInput;
};


export type Mutationupdate_nodeArgs = {
  diagram_id: Scalars['ID']['input'];
  input: UpdateNodeInput;
  node_id: Scalars['ID']['input'];
};


export type Mutationupdate_node_stateArgs = {
  input: UpdateNodeStateInput;
};


export type Mutationupdate_personArgs = {
  id: Scalars['ID']['input'];
  input: UpdatePersonInput;
};


export type Mutationupload_diagramArgs = {
  file: Scalars['Upload']['input'];
  format: DiagramFormat;
};


export type Mutationupload_fileArgs = {
  file: Scalars['Upload']['input'];
  path?: InputMaybe<Scalars['String']['input']>;
};


export type Mutationvalidate_diagramArgs = {
  content: Scalars['String']['input'];
  format: DiagramFormat;
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
  api_key_id: Scalars['ID']['input'];
  model: Scalars['String']['input'];
  service: LLMService;
  system_prompt?: InputMaybe<Scalars['String']['input']>;
};

export type PersonLLMConfigType = {
  __typename?: 'PersonLLMConfigType';
  api_key_id: Scalars['String']['output'];
  model: Scalars['String']['output'];
  prompt_file?: Maybe<Scalars['String']['output']>;
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
  active_cli_session?: Maybe<CliSession>;
  api_key?: Maybe<DomainApiKeyType>;
  api_keys: Array<DomainApiKeyType>;
  available_models: Array<Scalars['String']['output']>;
  conversations: Scalars['JSON']['output'];
  diagram?: Maybe<DomainDiagramType>;
  diagrams: Array<DomainDiagramType>;
  execution?: Maybe<ExecutionStateType>;
  execution_capabilities: Scalars['JSON']['output'];
  execution_history: Array<ExecutionStateType>;
  execution_metrics?: Maybe<Scalars['JSON']['output']>;
  execution_order: Scalars['JSON']['output'];
  executions: Array<ExecutionStateType>;
  health: Scalars['JSON']['output'];
  person?: Maybe<DomainPersonType>;
  persons: Array<DomainPersonType>;
  prompt_file: Scalars['JSON']['output'];
  prompt_files: Array<Scalars['JSON']['output']>;
  supported_formats: Array<DiagramFormatInfo>;
  system_info: Scalars['JSON']['output'];
};


export type Queryapi_keyArgs = {
  id: Scalars['ID']['input'];
};


export type Queryapi_keysArgs = {
  service?: InputMaybe<Scalars['String']['input']>;
};


export type Queryavailable_modelsArgs = {
  api_key_id: Scalars['ID']['input'];
  service: Scalars['String']['input'];
};


export type QueryconversationsArgs = {
  execution_id?: InputMaybe<Scalars['ID']['input']>;
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
  person_id?: InputMaybe<Scalars['ID']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  show_forgotten?: Scalars['Boolean']['input'];
  since?: InputMaybe<Scalars['DateTime']['input']>;
};


export type QuerydiagramArgs = {
  id: Scalars['ID']['input'];
};


export type QuerydiagramsArgs = {
  filter?: InputMaybe<DiagramFilterInput>;
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
};


export type QueryexecutionArgs = {
  id: Scalars['ID']['input'];
};


export type Queryexecution_historyArgs = {
  diagram_id?: InputMaybe<Scalars['ID']['input']>;
  include_metrics?: Scalars['Boolean']['input'];
  limit?: Scalars['Int']['input'];
};


export type Queryexecution_metricsArgs = {
  execution_id: Scalars['ID']['input'];
};


export type Queryexecution_orderArgs = {
  execution_id: Scalars['ID']['input'];
};


export type QueryexecutionsArgs = {
  filter?: InputMaybe<ExecutionFilterInput>;
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
};


export type QuerypersonArgs = {
  id: Scalars['ID']['input'];
};


export type QuerypersonsArgs = {
  limit?: Scalars['Int']['input'];
};


export type Queryprompt_fileArgs = {
  filename: Scalars['String']['input'];
};

export type RegisterCliSessionInput = {
  diagram_data?: InputMaybe<Scalars['JSON']['input']>;
  diagram_format: Scalars['String']['input'];
  diagram_name: Scalars['String']['input'];
  execution_id: Scalars['String']['input'];
};

export { Status };

export type Subscription = {
  __typename?: 'Subscription';
  execution_logs: Scalars['JSON']['output'];
  execution_updates: ExecutionUpdate;
  interactive_prompts: Scalars['JSON']['output'];
  node_updates: Scalars['JSON']['output'];
};


export type Subscriptionexecution_logsArgs = {
  execution_id: Scalars['ID']['input'];
};


export type Subscriptionexecution_updatesArgs = {
  execution_id: Scalars['ID']['input'];
};


export type Subscriptioninteractive_promptsArgs = {
  execution_id: Scalars['ID']['input'];
};


export type Subscriptionnode_updatesArgs = {
  execution_id: Scalars['ID']['input'];
  node_id?: InputMaybe<Scalars['String']['input']>;
};

export type TestApiKeyResult = {
  __typename?: 'TestApiKeyResult';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  model_info?: Maybe<Scalars['JSON']['output']>;
  success: Scalars['Boolean']['output'];
};

export type TokenUsageType = {
  __typename?: 'TokenUsageType';
  cached?: Maybe<Scalars['Int']['output']>;
  input: Scalars['Int']['output'];
  output: Scalars['Int']['output'];
  total?: Maybe<Scalars['Int']['output']>;
};

export type UnregisterCliSessionInput = {
  execution_id: Scalars['String']['input'];
};

export type UpdateNodeInput = {
  data?: InputMaybe<Scalars['JSON']['input']>;
  position?: InputMaybe<Vec2Input>;
};

export type UpdateNodeStateInput = {
  error?: InputMaybe<Scalars['String']['input']>;
  execution_id: Scalars['ID']['input'];
  node_id: Scalars['ID']['input'];
  output?: InputMaybe<Scalars['JSON']['input']>;
  status: Status;
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


export type GetApiKeysQuery = { __typename?: 'Query', api_keys: Array<{ __typename?: 'DomainApiKeyType', id: string, label: string, service: APIServiceType, key?: string | null }> };

export type GetApiKeyQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetApiKeyQuery = { __typename?: 'Query', api_key?: { __typename?: 'DomainApiKeyType', id: string, label: string, service: APIServiceType } | null };

export type GetAvailableModelsQueryVariables = Exact<{
  service: Scalars['String']['input'];
  apiKeyId: Scalars['ID']['input'];
}>;


export type GetAvailableModelsQuery = { __typename?: 'Query', available_models: Array<string> };

export type CreateApiKeyMutationVariables = Exact<{
  input: CreateApiKeyInput;
}>;


export type CreateApiKeyMutation = { __typename?: 'Mutation', create_api_key: { __typename?: 'ApiKeyResult', success: boolean, message?: string | null, error?: string | null, api_key?: { __typename?: 'DomainApiKeyType', id: string, label: string, service: APIServiceType } | null } };

export type TestApiKeyMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type TestApiKeyMutation = { __typename?: 'Mutation', test_api_key: { __typename?: 'TestApiKeyResult', success: boolean, message?: string | null, error?: string | null } };

export type DeleteApiKeyMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type DeleteApiKeyMutation = { __typename?: 'Mutation', delete_api_key: { __typename?: 'DeleteResult', success: boolean, message?: string | null } };

export type GetConversationsQueryVariables = Exact<{
  person_id?: InputMaybe<Scalars['ID']['input']>;
  execution_id?: InputMaybe<Scalars['ID']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  show_forgotten?: InputMaybe<Scalars['Boolean']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  since?: InputMaybe<Scalars['DateTime']['input']>;
}>;


export type GetConversationsQuery = { __typename?: 'Query', conversations: any };

export type GetDiagramQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetDiagramQuery = { __typename?: 'Query', diagram?: { __typename?: 'DomainDiagramType', nodes: Array<{ __typename?: 'DomainNodeType', id: string, type: NodeType, data: any, position: { __typename?: 'Vec2Type', x: number, y: number } }>, handles: Array<{ __typename?: 'DomainHandleType', id: string, node_id: string, label: HandleLabel, direction: HandleDirection, data_type: DataType, position?: string | null }>, arrows: Array<{ __typename?: 'DomainArrowType', id: string, source: string, target: string, content_type?: ContentType | null, label?: string | null, data?: any | null }>, persons: Array<{ __typename?: 'DomainPersonType', id: string, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } }>, metadata?: { __typename?: 'DiagramMetadataType', id?: string | null, name?: string | null, description?: string | null, version: string, created: string, modified: string, author?: string | null, tags?: Array<string> | null } | null } | null };

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
  input: ExecuteDiagramInput;
}>;


export type ExecuteDiagramMutation = { __typename?: 'Mutation', execute_diagram: { __typename?: 'ExecutionResult', success: boolean, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionStateType', id: string } | null } };

export type DeleteDiagramMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type DeleteDiagramMutation = { __typename?: 'Mutation', delete_diagram: { __typename?: 'DeleteResult', success: boolean, message?: string | null, error?: string | null } };

export type GetExecutionQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetExecutionQuery = { __typename?: 'Query', execution?: { __typename?: 'ExecutionStateType', id: string, status: Status, diagram_id?: string | null, started_at: string, ended_at?: string | null, node_states: any, node_outputs: any, variables?: any | null, error?: string | null, duration_seconds?: number | null, is_active?: boolean | null, token_usage: { __typename?: 'TokenUsageType', input: number, output: number, cached?: number | null } } | null };

export type ListExecutionsQueryVariables = Exact<{
  filter?: InputMaybe<ExecutionFilterInput>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ListExecutionsQuery = { __typename?: 'Query', executions: Array<{ __typename?: 'ExecutionStateType', id: string, status: Status, diagram_id?: string | null, started_at: string, ended_at?: string | null, is_active?: boolean | null, duration_seconds?: number | null }> };

export type ExecutionOrderQueryVariables = Exact<{
  executionId: Scalars['ID']['input'];
}>;


export type ExecutionOrderQuery = { __typename?: 'Query', execution_order: any };

export type ExecutionUpdatesSubscriptionVariables = Exact<{
  executionId: Scalars['ID']['input'];
}>;


export type ExecutionUpdatesSubscription = { __typename?: 'Subscription', execution_updates: { __typename?: 'ExecutionUpdate', execution_id: string, event_type: string, data: any, timestamp: string } };

export type NodeUpdatesSubscriptionVariables = Exact<{
  executionId: Scalars['ID']['input'];
  nodeId?: InputMaybe<Scalars['String']['input']>;
}>;


export type NodeUpdatesSubscription = { __typename?: 'Subscription', node_updates: any };

export type InteractivePromptsSubscriptionVariables = Exact<{
  executionId: Scalars['ID']['input'];
}>;


export type InteractivePromptsSubscription = { __typename?: 'Subscription', interactive_prompts: any };

export type ExecutionLogsSubscriptionVariables = Exact<{
  executionId: Scalars['ID']['input'];
}>;


export type ExecutionLogsSubscription = { __typename?: 'Subscription', execution_logs: any };

export type ControlExecutionMutationVariables = Exact<{
  input: ExecutionControlInput;
}>;


export type ControlExecutionMutation = { __typename?: 'Mutation', control_execution: { __typename?: 'ExecutionResult', success: boolean, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionStateType', id: string, status: Status } | null } };

export type SendInteractiveResponseMutationVariables = Exact<{
  input: InteractiveResponseInput;
}>;


export type SendInteractiveResponseMutation = { __typename?: 'Mutation', send_interactive_response: { __typename?: 'ExecutionResult', success: boolean, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionStateType', id: string, status: Status, node_states: any } | null } };

export type UploadFileMutationVariables = Exact<{
  file: Scalars['Upload']['input'];
  path?: InputMaybe<Scalars['String']['input']>;
}>;


export type UploadFileMutation = { __typename?: 'Mutation', upload_file: { __typename?: 'FileUploadResult', success: boolean, path?: string | null, size_bytes?: number | null, content_type?: string | null, message?: string | null, error?: string | null } };

export type ValidateDiagramMutationVariables = Exact<{
  content: Scalars['String']['input'];
  format: DiagramFormat;
}>;


export type ValidateDiagramMutation = { __typename?: 'Mutation', validate_diagram: { __typename?: 'DiagramValidationResult', success: boolean, message?: string | null, errors?: Array<string> | null, warnings?: Array<string> | null } };

export type ConvertDiagramFormatMutationVariables = Exact<{
  content: Scalars['String']['input'];
  fromFormat: DiagramFormat;
  toFormat: DiagramFormat;
}>;


export type ConvertDiagramFormatMutation = { __typename?: 'Mutation', convert_diagram_format: { __typename?: 'DiagramConvertResult', success: boolean, message?: string | null, error?: string | null, content?: string | null, format?: DiagramFormat | null } };

export type GetSupportedFormatsQueryVariables = Exact<{ [key: string]: never; }>;


export type GetSupportedFormatsQuery = { __typename?: 'Query', supported_formats: Array<{ __typename?: 'DiagramFormatInfo', format: string, name: string, extension: string, supports_export: boolean, supports_import: boolean, description?: string | null }> };

export type CreateNodeMutationVariables = Exact<{
  diagramId: Scalars['ID']['input'];
  input: CreateNodeInput;
}>;


export type CreateNodeMutation = { __typename?: 'Mutation', create_node: { __typename?: 'NodeResult', success: boolean, message?: string | null, error?: string | null, node?: { __typename?: 'DomainNodeType', id: string, type: NodeType, data: any, position: { __typename?: 'Vec2Type', x: number, y: number } } | null } };

export type UpdateNodeMutationVariables = Exact<{
  diagramId: Scalars['ID']['input'];
  nodeId: Scalars['ID']['input'];
  input: UpdateNodeInput;
}>;


export type UpdateNodeMutation = { __typename?: 'Mutation', update_node: { __typename?: 'NodeResult', success: boolean, message?: string | null, error?: string | null, node?: { __typename?: 'DomainNodeType', id: string, type: NodeType, data: any, position: { __typename?: 'Vec2Type', x: number, y: number } } | null } };

export type DeleteNodeMutationVariables = Exact<{
  diagramId: Scalars['ID']['input'];
  nodeId: Scalars['ID']['input'];
}>;


export type DeleteNodeMutation = { __typename?: 'Mutation', delete_node: { __typename?: 'DeleteResult', success: boolean, message?: string | null, error?: string | null } };

export type GetPersonQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetPersonQuery = { __typename?: 'Query', person?: { __typename?: 'DomainPersonType', id: string, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } } | null };

export type GetPersonsQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Int']['input']>;
}>;


export type GetPersonsQuery = { __typename?: 'Query', persons: Array<{ __typename?: 'DomainPersonType', id: string, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } }> };

export type CreatePersonMutationVariables = Exact<{
  input: CreatePersonInput;
}>;


export type CreatePersonMutation = { __typename?: 'Mutation', create_person: { __typename?: 'PersonResult', success: boolean, message?: string | null, error?: string | null, person?: { __typename?: 'DomainPersonType', id: string, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } } | null } };

export type UpdatePersonMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  input: UpdatePersonInput;
}>;


export type UpdatePersonMutation = { __typename?: 'Mutation', update_person: { __typename?: 'PersonResult', success: boolean, message?: string | null, error?: string | null, person?: { __typename?: 'DomainPersonType', id: string, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } } | null } };

export type DeletePersonMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type DeletePersonMutation = { __typename?: 'Mutation', delete_person: { __typename?: 'DeleteResult', success: boolean, message?: string | null, error?: string | null } };

export type GetPromptFilesQueryVariables = Exact<{ [key: string]: never; }>;


export type GetPromptFilesQuery = { __typename?: 'Query', prompt_files: Array<any> };

export type GetPromptFileQueryVariables = Exact<{
  filename: Scalars['String']['input'];
}>;


export type GetPromptFileQuery = { __typename?: 'Query', prompt_file: any };

export type GetSystemInfoQueryVariables = Exact<{ [key: string]: never; }>;


export type GetSystemInfoQuery = { __typename?: 'Query', system_info: any };

export type ActiveCliSessionQueryVariables = Exact<{ [key: string]: never; }>;


export type ActiveCliSessionQuery = { __typename?: 'Query', active_cli_session?: { __typename?: 'CliSession', session_id: string, execution_id: string, diagram_name: string, diagram_format: string, started_at: any, is_active: boolean, diagram_data?: string | null } | null };


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
    query GetApiKey($id: ID!) {
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
    query GetAvailableModels($service: String!, $apiKeyId: ID!) {
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
    mutation TestApiKey($id: ID!) {
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
    mutation DeleteApiKey($id: ID!) {
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
    query GetConversations($person_id: ID, $execution_id: ID, $search: String, $show_forgotten: Boolean = false, $limit: Int = 100, $offset: Int = 0, $since: DateTime) {
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
export const GetDiagramDocument = gql`
    query GetDiagram($id: ID!) {
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
    mutation ExecuteDiagram($input: ExecuteDiagramInput!) {
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
 *      input: // value for 'input'
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
    mutation DeleteDiagram($id: ID!) {
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
    query GetExecution($id: ID!) {
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
export const ExecutionOrderDocument = gql`
    query ExecutionOrder($executionId: ID!) {
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
export const ExecutionUpdatesDocument = gql`
    subscription ExecutionUpdates($executionId: ID!) {
  execution_updates(execution_id: $executionId) {
    execution_id
    event_type
    data
    timestamp
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
    subscription NodeUpdates($executionId: ID!, $nodeId: String) {
  node_updates(execution_id: $executionId, node_id: $nodeId)
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
 *      nodeId: // value for 'nodeId'
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
    subscription InteractivePrompts($executionId: ID!) {
  interactive_prompts(execution_id: $executionId)
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
export const ExecutionLogsDocument = gql`
    subscription ExecutionLogs($executionId: ID!) {
  execution_logs(execution_id: $executionId)
}
    `;

/**
 * __useExecutionLogsSubscription__
 *
 * To run a query within a React component, call `useExecutionLogsSubscription` and pass it any options that fit your needs.
 * When your component renders, `useExecutionLogsSubscription` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the subscription, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useExecutionLogsSubscription({
 *   variables: {
 *      executionId: // value for 'executionId'
 *   },
 * });
 */
export function useExecutionLogsSubscription(baseOptions: Apollo.SubscriptionHookOptions<ExecutionLogsSubscription, ExecutionLogsSubscriptionVariables> & ({ variables: ExecutionLogsSubscriptionVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useSubscription<ExecutionLogsSubscription, ExecutionLogsSubscriptionVariables>(ExecutionLogsDocument, options);
      }
export type ExecutionLogsSubscriptionHookResult = ReturnType<typeof useExecutionLogsSubscription>;
export type ExecutionLogsSubscriptionResult = Apollo.SubscriptionResult<ExecutionLogsSubscription>;
export const ControlExecutionDocument = gql`
    mutation ControlExecution($input: ExecutionControlInput!) {
  control_execution(input: $input) {
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
 *      input: // value for 'input'
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
export const SendInteractiveResponseDocument = gql`
    mutation SendInteractiveResponse($input: InteractiveResponseInput!) {
  send_interactive_response(input: $input) {
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
export type SendInteractiveResponseMutationFn = Apollo.MutationFunction<SendInteractiveResponseMutation, SendInteractiveResponseMutationVariables>;

/**
 * __useSendInteractiveResponseMutation__
 *
 * To run a mutation, you first call `useSendInteractiveResponseMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useSendInteractiveResponseMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [sendInteractiveResponseMutation, { data, loading, error }] = useSendInteractiveResponseMutation({
 *   variables: {
 *      input: // value for 'input'
 *   },
 * });
 */
export function useSendInteractiveResponseMutation(baseOptions?: Apollo.MutationHookOptions<SendInteractiveResponseMutation, SendInteractiveResponseMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<SendInteractiveResponseMutation, SendInteractiveResponseMutationVariables>(SendInteractiveResponseDocument, options);
      }
export type SendInteractiveResponseMutationHookResult = ReturnType<typeof useSendInteractiveResponseMutation>;
export type SendInteractiveResponseMutationResult = Apollo.MutationResult<SendInteractiveResponseMutation>;
export type SendInteractiveResponseMutationOptions = Apollo.BaseMutationOptions<SendInteractiveResponseMutation, SendInteractiveResponseMutationVariables>;
export const UploadFileDocument = gql`
    mutation UploadFile($file: Upload!, $path: String) {
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
 *      path: // value for 'path'
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
    mutation ValidateDiagram($content: String!, $format: DiagramFormat!) {
  validate_diagram(content: $content, format: $format) {
    success
    message
    errors
    warnings
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
 *      content: // value for 'content'
 *      format: // value for 'format'
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
export const ConvertDiagramFormatDocument = gql`
    mutation ConvertDiagramFormat($content: String!, $fromFormat: DiagramFormat!, $toFormat: DiagramFormat!) {
  convert_diagram_format(
    content: $content
    from_format: $fromFormat
    to_format: $toFormat
  ) {
    success
    message
    error
    content
    format
    format
  }
}
    `;
export type ConvertDiagramFormatMutationFn = Apollo.MutationFunction<ConvertDiagramFormatMutation, ConvertDiagramFormatMutationVariables>;

/**
 * __useConvertDiagramFormatMutation__
 *
 * To run a mutation, you first call `useConvertDiagramFormatMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useConvertDiagramFormatMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [convertDiagramFormatMutation, { data, loading, error }] = useConvertDiagramFormatMutation({
 *   variables: {
 *      content: // value for 'content'
 *      fromFormat: // value for 'fromFormat'
 *      toFormat: // value for 'toFormat'
 *   },
 * });
 */
export function useConvertDiagramFormatMutation(baseOptions?: Apollo.MutationHookOptions<ConvertDiagramFormatMutation, ConvertDiagramFormatMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<ConvertDiagramFormatMutation, ConvertDiagramFormatMutationVariables>(ConvertDiagramFormatDocument, options);
      }
export type ConvertDiagramFormatMutationHookResult = ReturnType<typeof useConvertDiagramFormatMutation>;
export type ConvertDiagramFormatMutationResult = Apollo.MutationResult<ConvertDiagramFormatMutation>;
export type ConvertDiagramFormatMutationOptions = Apollo.BaseMutationOptions<ConvertDiagramFormatMutation, ConvertDiagramFormatMutationVariables>;
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
    mutation CreateNode($diagramId: ID!, $input: CreateNodeInput!) {
  create_node(diagram_id: $diagramId, input: $input) {
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
 *      input: // value for 'input'
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
    mutation UpdateNode($diagramId: ID!, $nodeId: ID!, $input: UpdateNodeInput!) {
  update_node(diagram_id: $diagramId, node_id: $nodeId, input: $input) {
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
 *      diagramId: // value for 'diagramId'
 *      nodeId: // value for 'nodeId'
 *      input: // value for 'input'
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
    mutation DeleteNode($diagramId: ID!, $nodeId: ID!) {
  delete_node(diagram_id: $diagramId, node_id: $nodeId) {
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
 *      diagramId: // value for 'diagramId'
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
    query GetPerson($id: ID!) {
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
    mutation CreatePerson($input: CreatePersonInput!) {
  create_person(input: $input) {
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
 *      input: // value for 'input'
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
    mutation UpdatePerson($id: ID!, $input: UpdatePersonInput!) {
  update_person(id: $id, input: $input) {
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
 *      id: // value for 'id'
 *      input: // value for 'input'
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
    mutation DeletePerson($id: ID!) {
  delete_person(id: $id) {
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
 *      id: // value for 'id'
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
export const ActiveCliSessionDocument = gql`
    query ActiveCliSession {
  active_cli_session {
    session_id
    execution_id
    diagram_name
    diagram_format
    started_at
    is_active
    diagram_data
  }
}
    `;

/**
 * __useActiveCliSessionQuery__
 *
 * To run a query within a React component, call `useActiveCliSessionQuery` and pass it any options that fit your needs.
 * When your component renders, `useActiveCliSessionQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useActiveCliSessionQuery({
 *   variables: {
 *   },
 * });
 */
export function useActiveCliSessionQuery(baseOptions?: Apollo.QueryHookOptions<ActiveCliSessionQuery, ActiveCliSessionQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ActiveCliSessionQuery, ActiveCliSessionQueryVariables>(ActiveCliSessionDocument, options);
      }
export function useActiveCliSessionLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ActiveCliSessionQuery, ActiveCliSessionQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ActiveCliSessionQuery, ActiveCliSessionQueryVariables>(ActiveCliSessionDocument, options);
        }
export function useActiveCliSessionSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ActiveCliSessionQuery, ActiveCliSessionQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ActiveCliSessionQuery, ActiveCliSessionQueryVariables>(ActiveCliSessionDocument, options);
        }
export type ActiveCliSessionQueryHookResult = ReturnType<typeof useActiveCliSessionQuery>;
export type ActiveCliSessionLazyQueryHookResult = ReturnType<typeof useActiveCliSessionLazyQuery>;
export type ActiveCliSessionSuspenseQueryHookResult = ReturnType<typeof useActiveCliSessionSuspenseQuery>;
export type ActiveCliSessionQueryResult = Apollo.QueryResult<ActiveCliSessionQuery, ActiveCliSessionQueryVariables>;