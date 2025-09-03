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
  CLAUDE_CODE = 'CLAUDE_CODE',
  DEEPSEEK = 'DEEPSEEK',
  GEMINI = 'GEMINI',
  GOOGLE = 'GOOGLE',
  OLLAMA = 'OLLAMA',
  OPENAI = 'OPENAI',
  VERTEX = 'VERTEX'
}

export type ApiKeyResult = {
  __typename?: 'ApiKeyResult';
  api_key?: Maybe<DomainApiKeyType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type AuthConfigType = {
  __typename?: 'AuthConfigType';
  format?: Maybe<Scalars['String']['output']>;
  header?: Maybe<Scalars['String']['output']>;
  query_param?: Maybe<Scalars['String']['output']>;
  scopes?: Maybe<Array<Scalars['String']['output']>>;
  strategy: Scalars['String']['output'];
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
  BINARY = 'BINARY',
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
  type: Scalars['String']['output'];
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
  llm_usage: LLMUsageType;
  metrics?: Maybe<Scalars['JSON']['output']>;
  node_outputs: Scalars['JSON']['output'];
  node_states: Scalars['JSON']['output'];
  started_at: Scalars['String']['output'];
  status: Status;
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

export type LLMUsageType = {
  __typename?: 'LLMUsageType';
  cached?: Maybe<Scalars['Int']['output']>;
  input: Scalars['Int']['output'];
  output: Scalars['Int']['output'];
  total?: Maybe<Scalars['Int']['output']>;
};

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

export type OperationSchemaType = {
  __typename?: 'OperationSchemaType';
  description?: Maybe<Scalars['String']['output']>;
  method: Scalars['String']['output'];
  operation: Scalars['String']['output'];
  path: Scalars['String']['output'];
  query_params?: Maybe<Scalars['JSON']['output']>;
  request_body?: Maybe<Scalars['JSON']['output']>;
  response?: Maybe<Scalars['JSON']['output']>;
};

export type OperationType = {
  __typename?: 'OperationType';
  description?: Maybe<Scalars['String']['output']>;
  has_pagination: Scalars['Boolean']['output'];
  method: Scalars['String']['output'];
  name: Scalars['String']['output'];
  path: Scalars['String']['output'];
  required_scopes?: Maybe<Array<Scalars['String']['output']>>;
  timeout_override?: Maybe<Scalars['Float']['output']>;
};

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

export type ProviderMetadataType = {
  __typename?: 'ProviderMetadataType';
  description?: Maybe<Scalars['String']['output']>;
  documentation_url?: Maybe<Scalars['String']['output']>;
  manifest_path?: Maybe<Scalars['String']['output']>;
  support_email?: Maybe<Scalars['String']['output']>;
  type: Scalars['String']['output'];
  version: Scalars['String']['output'];
};

export type ProviderStatisticsType = {
  __typename?: 'ProviderStatisticsType';
  provider_types: Scalars['JSON']['output'];
  providers: Array<Scalars['JSON']['output']>;
  total_operations: Scalars['Int']['output'];
  total_providers: Scalars['Int']['output'];
};

export type ProviderType = {
  __typename?: 'ProviderType';
  auth_config?: Maybe<AuthConfigType>;
  base_url?: Maybe<Scalars['String']['output']>;
  default_timeout: Scalars['Float']['output'];
  metadata: ProviderMetadataType;
  name: Scalars['String']['output'];
  operations: Array<OperationType>;
  rate_limit?: Maybe<RateLimitConfigType>;
  retry_policy?: Maybe<RetryPolicyType>;
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
  operation_schema?: Maybe<OperationSchemaType>;
  person?: Maybe<DomainPersonType>;
  persons: Array<DomainPersonType>;
  prompt_file: Scalars['JSON']['output'];
  prompt_files: Array<Scalars['JSON']['output']>;
  provider?: Maybe<ProviderType>;
  provider_operations: Array<OperationType>;
  provider_statistics: ProviderStatisticsType;
  providers: Array<ProviderType>;
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


export type Queryoperation_schemaArgs = {
  operation: Scalars['String']['input'];
  provider: Scalars['String']['input'];
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


export type QueryproviderArgs = {
  name: Scalars['String']['input'];
};


export type Queryprovider_operationsArgs = {
  provider: Scalars['String']['input'];
};

export type RateLimitConfigType = {
  __typename?: 'RateLimitConfigType';
  algorithm: Scalars['String']['output'];
  capacity: Scalars['Int']['output'];
  refill_per_sec: Scalars['Float']['output'];
  window_size_sec?: Maybe<Scalars['Int']['output']>;
};

export type RegisterCliSessionInput = {
  diagram_data?: InputMaybe<Scalars['JSON']['input']>;
  diagram_format: Scalars['String']['input'];
  diagram_name: Scalars['String']['input'];
  diagram_path?: InputMaybe<Scalars['String']['input']>;
  execution_id: Scalars['String']['input'];
};

export type RetryPolicyType = {
  __typename?: 'RetryPolicyType';
  base_delay_ms: Scalars['Int']['output'];
  max_delay_ms?: Maybe<Scalars['Int']['output']>;
  max_retries: Scalars['Int']['output'];
  retry_on_status: Array<Scalars['Int']['output']>;
  strategy: Scalars['String']['output'];
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

export type ControlExecutionMutationVariables = Exact<{
  input: ExecutionControlInput;
}>;


export type ControlExecutionMutation = { __typename?: 'Mutation', control_execution: { __typename?: 'ExecutionResult', success: boolean, execution_id?: string | null, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionStateType', id: string, status: Status } | null } };

export type ConvertDiagramFormatMutationVariables = Exact<{
  content: Scalars['String']['input'];
  from_format: DiagramFormat;
  to_format: DiagramFormat;
}>;


export type ConvertDiagramFormatMutation = { __typename?: 'Mutation', convert_diagram_format: { __typename?: 'DiagramConvertResult', success: boolean, content?: string | null, format?: DiagramFormat | null, message?: string | null, error?: string | null } };

export type CreateApiKeyMutationVariables = Exact<{
  input: CreateApiKeyInput;
}>;


export type CreateApiKeyMutation = { __typename?: 'Mutation', create_api_key: { __typename?: 'ApiKeyResult', success: boolean, message?: string | null, error?: string | null, api_key?: { __typename?: 'DomainApiKeyType', id: string, label: string, service: APIServiceType } | null } };

export type CreateDiagramMutationVariables = Exact<{
  input: CreateDiagramInput;
}>;


export type CreateDiagramMutation = { __typename?: 'Mutation', create_diagram: { __typename?: 'DiagramResult', success: boolean, message?: string | null, error?: string | null, diagram?: { __typename?: 'DomainDiagramType', metadata?: { __typename?: 'DiagramMetadataType', id?: string | null, name?: string | null } | null } | null } };

export type CreateNodeMutationVariables = Exact<{
  diagram_id: Scalars['ID']['input'];
  input: CreateNodeInput;
}>;


export type CreateNodeMutation = { __typename?: 'Mutation', create_node: { __typename?: 'NodeResult', success: boolean, message?: string | null, error?: string | null, node?: { __typename?: 'DomainNodeType', id: string, type: string, data: any, position: { __typename?: 'Vec2Type', x: number, y: number } } | null } };

export type CreatePersonMutationVariables = Exact<{
  input: CreatePersonInput;
}>;


export type CreatePersonMutation = { __typename?: 'Mutation', create_person: { __typename?: 'PersonResult', success: boolean, message?: string | null, error?: string | null, person?: { __typename?: 'DomainPersonType', id: string, label: string } | null } };

export type DeleteApiKeyMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type DeleteApiKeyMutation = { __typename?: 'Mutation', delete_api_key: { __typename?: 'DeleteResult', success: boolean, message?: string | null } };

export type DeleteDiagramMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type DeleteDiagramMutation = { __typename?: 'Mutation', delete_diagram: { __typename?: 'DeleteResult', success: boolean, message?: string | null, error?: string | null } };

export type DeleteNodeMutationVariables = Exact<{
  diagram_id: Scalars['ID']['input'];
  node_id: Scalars['ID']['input'];
}>;


export type DeleteNodeMutation = { __typename?: 'Mutation', delete_node: { __typename?: 'DeleteResult', success: boolean, message?: string | null, error?: string | null } };

export type DeletePersonMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type DeletePersonMutation = { __typename?: 'Mutation', delete_person: { __typename?: 'DeleteResult', success: boolean, message?: string | null, error?: string | null } };

export type ExecuteDiagramMutationVariables = Exact<{
  input: ExecuteDiagramInput;
}>;


export type ExecuteDiagramMutation = { __typename?: 'Mutation', execute_diagram: { __typename?: 'ExecutionResult', success: boolean, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionStateType', id: string } | null } };

export type RegisterCliSessionMutationVariables = Exact<{
  input: RegisterCliSessionInput;
}>;


export type RegisterCliSessionMutation = { __typename?: 'Mutation', register_cli_session: { __typename?: 'CliSessionResult', success: boolean, message?: string | null, error?: string | null } };

export type SendInteractiveResponseMutationVariables = Exact<{
  input: InteractiveResponseInput;
}>;


export type SendInteractiveResponseMutation = { __typename?: 'Mutation', send_interactive_response: { __typename?: 'ExecutionResult', success: boolean, execution_id?: string | null, message?: string | null, error?: string | null } };

export type TestApiKeyMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type TestApiKeyMutation = { __typename?: 'Mutation', test_api_key: { __typename?: 'TestApiKeyResult', success: boolean, message?: string | null, error?: string | null } };

export type UnregisterCliSessionMutationVariables = Exact<{
  input: UnregisterCliSessionInput;
}>;


export type UnregisterCliSessionMutation = { __typename?: 'Mutation', unregister_cli_session: { __typename?: 'CliSessionResult', success: boolean, message?: string | null, error?: string | null } };

export type UpdateNodeMutationVariables = Exact<{
  diagram_id: Scalars['ID']['input'];
  node_id: Scalars['ID']['input'];
  input: UpdateNodeInput;
}>;


export type UpdateNodeMutation = { __typename?: 'Mutation', update_node: { __typename?: 'NodeResult', success: boolean, message?: string | null, error?: string | null } };

export type UpdateNodeStateMutationVariables = Exact<{
  input: UpdateNodeStateInput;
}>;


export type UpdateNodeStateMutation = { __typename?: 'Mutation', update_node_state: { __typename?: 'ExecutionResult', success: boolean, execution_id?: string | null, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionStateType', id: string, status: Status } | null } };

export type UpdatePersonMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  input: UpdatePersonInput;
}>;


export type UpdatePersonMutation = { __typename?: 'Mutation', update_person: { __typename?: 'PersonResult', success: boolean, message?: string | null, error?: string | null, person?: { __typename?: 'DomainPersonType', id: string, label: string } | null } };

export type UploadDiagramMutationVariables = Exact<{
  file: Scalars['Upload']['input'];
  format: DiagramFormat;
}>;


export type UploadDiagramMutation = { __typename?: 'Mutation', upload_diagram: { __typename?: 'DiagramResult', success: boolean, message?: string | null, error?: string | null, diagram?: { __typename?: 'DomainDiagramType', metadata?: { __typename?: 'DiagramMetadataType', id?: string | null, name?: string | null } | null } | null } };

export type UploadFileMutationVariables = Exact<{
  file: Scalars['Upload']['input'];
  path?: InputMaybe<Scalars['String']['input']>;
}>;


export type UploadFileMutation = { __typename?: 'Mutation', upload_file: { __typename?: 'FileUploadResult', success: boolean, path?: string | null, size_bytes?: number | null, content_type?: string | null, message?: string | null, error?: string | null } };

export type ValidateDiagramMutationVariables = Exact<{
  content: Scalars['String']['input'];
  format: DiagramFormat;
}>;


export type ValidateDiagramMutation = { __typename?: 'Mutation', validate_diagram: { __typename?: 'DiagramValidationResult', success: boolean, errors?: Array<string> | null, warnings?: Array<string> | null, message?: string | null } };

export type GetActiveCliSessionQueryVariables = Exact<{ [key: string]: never; }>;


export type GetActiveCliSessionQuery = { __typename?: 'Query', active_cli_session?: { __typename?: 'CliSession', execution_id: string, diagram_name: string, diagram_format: string, started_at: any, is_active: boolean, diagram_data?: string | null } | null };

export type GetApiKeyQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetApiKeyQuery = { __typename?: 'Query', api_key?: { __typename?: 'DomainApiKeyType', id: string, label: string, service: APIServiceType } | null };

export type GetApiKeysQueryVariables = Exact<{
  service?: InputMaybe<Scalars['String']['input']>;
}>;


export type GetApiKeysQuery = { __typename?: 'Query', api_keys: Array<{ __typename?: 'DomainApiKeyType', id: string, label: string, service: APIServiceType, key?: string | null }> };

export type GetAvailableModelsQueryVariables = Exact<{
  service: Scalars['String']['input'];
  apiKeyId: Scalars['ID']['input'];
}>;


export type GetAvailableModelsQuery = { __typename?: 'Query', available_models: Array<string> };

export type GetDiagramQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetDiagramQuery = { __typename?: 'Query', diagram?: { __typename?: 'DomainDiagramType', nodes: Array<{ __typename?: 'DomainNodeType', id: string, type: string, data: any, position: { __typename?: 'Vec2Type', x: number, y: number } }>, handles: Array<{ __typename?: 'DomainHandleType', id: string, node_id: string, label: HandleLabel, direction: HandleDirection, data_type: DataType, position?: string | null }>, arrows: Array<{ __typename?: 'DomainArrowType', id: string, source: string, target: string, content_type?: ContentType | null, label?: string | null, data?: any | null }>, persons: Array<{ __typename?: 'DomainPersonType', id: string, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } }>, metadata?: { __typename?: 'DiagramMetadataType', id?: string | null, name?: string | null, description?: string | null, version: string, created: string, modified: string, author?: string | null, tags?: Array<string> | null } | null } | null };

export type GetExecutionQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetExecutionQuery = { __typename?: 'Query', execution?: { __typename?: 'ExecutionStateType', id: string, status: Status, diagram_id?: string | null, started_at: string, ended_at?: string | null, error?: string | null, node_states: any, node_outputs: any, variables?: any | null, metrics?: any | null } | null };

export type GetExecutionCapabilitiesQueryVariables = Exact<{ [key: string]: never; }>;


export type GetExecutionCapabilitiesQuery = { __typename?: 'Query', execution_capabilities: any };

export type GetExecutionHistoryQueryVariables = Exact<{
  diagram_id?: InputMaybe<Scalars['ID']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  include_metrics?: InputMaybe<Scalars['Boolean']['input']>;
}>;


export type GetExecutionHistoryQuery = { __typename?: 'Query', execution_history: Array<{ __typename?: 'ExecutionStateType', id: string, status: Status, diagram_id?: string | null, started_at: string, ended_at?: string | null, error?: string | null, metrics?: any | null }> };

export type GetExecutionMetricsQueryVariables = Exact<{
  execution_id: Scalars['ID']['input'];
}>;


export type GetExecutionMetricsQuery = { __typename?: 'Query', execution_metrics?: any | null };

export type GetExecutionOrderQueryVariables = Exact<{
  execution_id: Scalars['ID']['input'];
}>;


export type GetExecutionOrderQuery = { __typename?: 'Query', execution_order: any };

export type GetPersonQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetPersonQuery = { __typename?: 'Query', person?: { __typename?: 'DomainPersonType', id: string, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string, system_prompt?: string | null } } | null };

export type GetPromptFileQueryVariables = Exact<{
  filename: Scalars['String']['input'];
}>;


export type GetPromptFileQuery = { __typename?: 'Query', prompt_file: any };

export type GetSupportedFormatsQueryVariables = Exact<{ [key: string]: never; }>;


export type GetSupportedFormatsQuery = { __typename?: 'Query', supported_formats: Array<{ __typename?: 'DiagramFormatInfo', format: string, name: string, description?: string | null, extension: string, supports_import: boolean, supports_export: boolean }> };

export type GetSystemInfoQueryVariables = Exact<{ [key: string]: never; }>;


export type GetSystemInfoQuery = { __typename?: 'Query', system_info: any };

export type HealthCheckQueryVariables = Exact<{ [key: string]: never; }>;


export type HealthCheckQuery = { __typename?: 'Query', health: any };

export type ListConversationsQueryVariables = Exact<{
  person_id?: InputMaybe<Scalars['ID']['input']>;
  execution_id?: InputMaybe<Scalars['ID']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  show_forgotten?: InputMaybe<Scalars['Boolean']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  since?: InputMaybe<Scalars['DateTime']['input']>;
}>;


export type ListConversationsQuery = { __typename?: 'Query', conversations: any };

export type ListDiagramsQueryVariables = Exact<{
  filter?: InputMaybe<DiagramFilterInput>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ListDiagramsQuery = { __typename?: 'Query', diagrams: Array<{ __typename?: 'DomainDiagramType', nodeCount: number, arrowCount: number, metadata?: { __typename?: 'DiagramMetadataType', id?: string | null, name?: string | null, description?: string | null, author?: string | null, created: string, modified: string, tags?: Array<string> | null } | null }> };

export type ListExecutionsQueryVariables = Exact<{
  filter?: InputMaybe<ExecutionFilterInput>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ListExecutionsQuery = { __typename?: 'Query', executions: Array<{ __typename?: 'ExecutionStateType', id: string, status: Status, diagram_id?: string | null, started_at: string, ended_at?: string | null, error?: string | null }> };

export type ListPersonsQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ListPersonsQuery = { __typename?: 'Query', persons: Array<{ __typename?: 'DomainPersonType', id: string, label: string, type: string, llm_config: { __typename?: 'PersonLLMConfigType', service: LLMService, model: string, api_key_id: string } }> };

export type ListPromptFilesQueryVariables = Exact<{ [key: string]: never; }>;


export type ListPromptFilesQuery = { __typename?: 'Query', prompt_files: Array<any> };

export type ExecutionUpdatesSubscriptionVariables = Exact<{
  execution_id: Scalars['ID']['input'];
}>;


export type ExecutionUpdatesSubscription = { __typename?: 'Subscription', execution_updates: { __typename?: 'ExecutionUpdate', execution_id: string, event_type: string, data: any, timestamp: string } };

export type ProvidersQueryVariables = Exact<{ [key: string]: never; }>;


export type ProvidersQuery = { __typename?: 'Query', providers: Array<{ __typename?: 'ProviderType', name: string, metadata: { __typename?: 'ProviderMetadataType', description?: string | null } }> };

export type ProviderOpsQueryVariables = Exact<{
  provider: Scalars['String']['input'];
}>;


export type ProviderOpsQuery = { __typename?: 'Query', provider_operations: Array<{ __typename?: 'OperationType', name: string, description?: string | null }> };

export type ActiveCliSessionQueryVariables = Exact<{ [key: string]: never; }>;


export type ActiveCliSessionQuery = { __typename?: 'Query', active_cli_session?: { __typename?: 'CliSession', session_id: string, execution_id: string, diagram_name: string, diagram_format: string, started_at: any, is_active: boolean, diagram_data?: string | null } | null };

export type GetExecutionStateQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetExecutionStateQuery = { __typename?: 'Query', execution?: { __typename?: 'ExecutionStateType', id: string, status: Status, started_at: string, ended_at?: string | null, node_states: any, node_outputs: any } | null };

export type GetProvidersQueryVariables = Exact<{ [key: string]: never; }>;


export type GetProvidersQuery = { __typename?: 'Query', providers: Array<{ __typename?: 'ProviderType', name: string, base_url?: string | null, default_timeout: number, operations: Array<{ __typename?: 'OperationType', name: string, method: string, path: string, description?: string | null, required_scopes?: Array<string> | null }>, metadata: { __typename?: 'ProviderMetadataType', version: string, type: string, description?: string | null, documentation_url?: string | null } }> };

export type GetProviderOperationsQueryVariables = Exact<{
  provider: Scalars['String']['input'];
}>;


export type GetProviderOperationsQuery = { __typename?: 'Query', provider_operations: Array<{ __typename?: 'OperationType', name: string, method: string, path: string, description?: string | null, required_scopes?: Array<string> | null, has_pagination: boolean, timeout_override?: number | null }> };

export type GetOperationSchemaQueryVariables = Exact<{
  provider: Scalars['String']['input'];
  operation: Scalars['String']['input'];
}>;


export type GetOperationSchemaQuery = { __typename?: 'Query', operation_schema?: { __typename?: 'OperationSchemaType', operation: string, method: string, path: string, description?: string | null, request_body?: any | null, query_params?: any | null, response?: any | null } | null };

export type ListRecentExecutionsQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ListRecentExecutionsQuery = { __typename?: 'Query', executions: Array<{ __typename?: 'ExecutionStateType', id: string, diagram_id?: string | null, status: Status, started_at: string, ended_at?: string | null, error?: string | null }> };

export type ListActiveExecutionsQueryVariables = Exact<{
  filter?: InputMaybe<ExecutionFilterInput>;
  limit?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ListActiveExecutionsQuery = { __typename?: 'Query', executions: Array<{ __typename?: 'ExecutionStateType', id: string, status: Status, diagram_id?: string | null, started_at: string, ended_at?: string | null }> };


export const ControlExecutionDocument = gql`
    mutation ControlExecution($input: ExecutionControlInput!) {
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
export const ConvertDiagramFormatDocument = gql`
    mutation ConvertDiagramFormat($content: String!, $from_format: DiagramFormat!, $to_format: DiagramFormat!) {
  convert_diagram_format(
    content: $content
    from_format: $from_format
    to_format: $to_format
  ) {
    success
    content
    format
    message
    error
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
 *      from_format: // value for 'from_format'
 *      to_format: // value for 'to_format'
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
export const CreateNodeDocument = gql`
    mutation CreateNode($diagram_id: ID!, $input: CreateNodeInput!) {
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
 *      diagram_id: // value for 'diagram_id'
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
export const CreatePersonDocument = gql`
    mutation CreatePerson($input: CreatePersonInput!) {
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
export const DeleteNodeDocument = gql`
    mutation DeleteNode($diagram_id: ID!, $node_id: ID!) {
  delete_node(diagram_id: $diagram_id, node_id: $node_id) {
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
 *      diagram_id: // value for 'diagram_id'
 *      node_id: // value for 'node_id'
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
export const RegisterCliSessionDocument = gql`
    mutation RegisterCliSession($input: RegisterCliSessionInput!) {
  register_cli_session(input: $input) {
    success
    message
    error
  }
}
    `;
export type RegisterCliSessionMutationFn = Apollo.MutationFunction<RegisterCliSessionMutation, RegisterCliSessionMutationVariables>;

/**
 * __useRegisterCliSessionMutation__
 *
 * To run a mutation, you first call `useRegisterCliSessionMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useRegisterCliSessionMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [registerCliSessionMutation, { data, loading, error }] = useRegisterCliSessionMutation({
 *   variables: {
 *      input: // value for 'input'
 *   },
 * });
 */
export function useRegisterCliSessionMutation(baseOptions?: Apollo.MutationHookOptions<RegisterCliSessionMutation, RegisterCliSessionMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<RegisterCliSessionMutation, RegisterCliSessionMutationVariables>(RegisterCliSessionDocument, options);
      }
export type RegisterCliSessionMutationHookResult = ReturnType<typeof useRegisterCliSessionMutation>;
export type RegisterCliSessionMutationResult = Apollo.MutationResult<RegisterCliSessionMutation>;
export type RegisterCliSessionMutationOptions = Apollo.BaseMutationOptions<RegisterCliSessionMutation, RegisterCliSessionMutationVariables>;
export const SendInteractiveResponseDocument = gql`
    mutation SendInteractiveResponse($input: InteractiveResponseInput!) {
  send_interactive_response(input: $input) {
    success
    execution_id
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
export const UnregisterCliSessionDocument = gql`
    mutation UnregisterCliSession($input: UnregisterCliSessionInput!) {
  unregister_cli_session(input: $input) {
    success
    message
    error
  }
}
    `;
export type UnregisterCliSessionMutationFn = Apollo.MutationFunction<UnregisterCliSessionMutation, UnregisterCliSessionMutationVariables>;

/**
 * __useUnregisterCliSessionMutation__
 *
 * To run a mutation, you first call `useUnregisterCliSessionMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useUnregisterCliSessionMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [unregisterCliSessionMutation, { data, loading, error }] = useUnregisterCliSessionMutation({
 *   variables: {
 *      input: // value for 'input'
 *   },
 * });
 */
export function useUnregisterCliSessionMutation(baseOptions?: Apollo.MutationHookOptions<UnregisterCliSessionMutation, UnregisterCliSessionMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<UnregisterCliSessionMutation, UnregisterCliSessionMutationVariables>(UnregisterCliSessionDocument, options);
      }
export type UnregisterCliSessionMutationHookResult = ReturnType<typeof useUnregisterCliSessionMutation>;
export type UnregisterCliSessionMutationResult = Apollo.MutationResult<UnregisterCliSessionMutation>;
export type UnregisterCliSessionMutationOptions = Apollo.BaseMutationOptions<UnregisterCliSessionMutation, UnregisterCliSessionMutationVariables>;
export const UpdateNodeDocument = gql`
    mutation UpdateNode($diagram_id: ID!, $node_id: ID!, $input: UpdateNodeInput!) {
  update_node(diagram_id: $diagram_id, node_id: $node_id, input: $input) {
    success
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
 *      diagram_id: // value for 'diagram_id'
 *      node_id: // value for 'node_id'
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
export const UpdateNodeStateDocument = gql`
    mutation UpdateNodeState($input: UpdateNodeStateInput!) {
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
export type UpdateNodeStateMutationFn = Apollo.MutationFunction<UpdateNodeStateMutation, UpdateNodeStateMutationVariables>;

/**
 * __useUpdateNodeStateMutation__
 *
 * To run a mutation, you first call `useUpdateNodeStateMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useUpdateNodeStateMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [updateNodeStateMutation, { data, loading, error }] = useUpdateNodeStateMutation({
 *   variables: {
 *      input: // value for 'input'
 *   },
 * });
 */
export function useUpdateNodeStateMutation(baseOptions?: Apollo.MutationHookOptions<UpdateNodeStateMutation, UpdateNodeStateMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<UpdateNodeStateMutation, UpdateNodeStateMutationVariables>(UpdateNodeStateDocument, options);
      }
export type UpdateNodeStateMutationHookResult = ReturnType<typeof useUpdateNodeStateMutation>;
export type UpdateNodeStateMutationResult = Apollo.MutationResult<UpdateNodeStateMutation>;
export type UpdateNodeStateMutationOptions = Apollo.BaseMutationOptions<UpdateNodeStateMutation, UpdateNodeStateMutationVariables>;
export const UpdatePersonDocument = gql`
    mutation UpdatePerson($id: ID!, $input: UpdatePersonInput!) {
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
export const UploadDiagramDocument = gql`
    mutation UploadDiagram($file: Upload!, $format: DiagramFormat!) {
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
export type UploadDiagramMutationFn = Apollo.MutationFunction<UploadDiagramMutation, UploadDiagramMutationVariables>;

/**
 * __useUploadDiagramMutation__
 *
 * To run a mutation, you first call `useUploadDiagramMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useUploadDiagramMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [uploadDiagramMutation, { data, loading, error }] = useUploadDiagramMutation({
 *   variables: {
 *      file: // value for 'file'
 *      format: // value for 'format'
 *   },
 * });
 */
export function useUploadDiagramMutation(baseOptions?: Apollo.MutationHookOptions<UploadDiagramMutation, UploadDiagramMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<UploadDiagramMutation, UploadDiagramMutationVariables>(UploadDiagramDocument, options);
      }
export type UploadDiagramMutationHookResult = ReturnType<typeof useUploadDiagramMutation>;
export type UploadDiagramMutationResult = Apollo.MutationResult<UploadDiagramMutation>;
export type UploadDiagramMutationOptions = Apollo.BaseMutationOptions<UploadDiagramMutation, UploadDiagramMutationVariables>;
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
    errors
    warnings
    message
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
export const GetActiveCliSessionDocument = gql`
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
    `;

/**
 * __useGetActiveCliSessionQuery__
 *
 * To run a query within a React component, call `useGetActiveCliSessionQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetActiveCliSessionQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetActiveCliSessionQuery({
 *   variables: {
 *   },
 * });
 */
export function useGetActiveCliSessionQuery(baseOptions?: Apollo.QueryHookOptions<GetActiveCliSessionQuery, GetActiveCliSessionQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetActiveCliSessionQuery, GetActiveCliSessionQueryVariables>(GetActiveCliSessionDocument, options);
      }
export function useGetActiveCliSessionLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetActiveCliSessionQuery, GetActiveCliSessionQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetActiveCliSessionQuery, GetActiveCliSessionQueryVariables>(GetActiveCliSessionDocument, options);
        }
export function useGetActiveCliSessionSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetActiveCliSessionQuery, GetActiveCliSessionQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetActiveCliSessionQuery, GetActiveCliSessionQueryVariables>(GetActiveCliSessionDocument, options);
        }
export type GetActiveCliSessionQueryHookResult = ReturnType<typeof useGetActiveCliSessionQuery>;
export type GetActiveCliSessionLazyQueryHookResult = ReturnType<typeof useGetActiveCliSessionLazyQuery>;
export type GetActiveCliSessionSuspenseQueryHookResult = ReturnType<typeof useGetActiveCliSessionSuspenseQuery>;
export type GetActiveCliSessionQueryResult = Apollo.QueryResult<GetActiveCliSessionQuery, GetActiveCliSessionQueryVariables>;
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
export const GetExecutionDocument = gql`
    query GetExecution($id: ID!) {
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
export const GetExecutionCapabilitiesDocument = gql`
    query GetExecutionCapabilities {
  execution_capabilities
}
    `;

/**
 * __useGetExecutionCapabilitiesQuery__
 *
 * To run a query within a React component, call `useGetExecutionCapabilitiesQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetExecutionCapabilitiesQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetExecutionCapabilitiesQuery({
 *   variables: {
 *   },
 * });
 */
export function useGetExecutionCapabilitiesQuery(baseOptions?: Apollo.QueryHookOptions<GetExecutionCapabilitiesQuery, GetExecutionCapabilitiesQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetExecutionCapabilitiesQuery, GetExecutionCapabilitiesQueryVariables>(GetExecutionCapabilitiesDocument, options);
      }
export function useGetExecutionCapabilitiesLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetExecutionCapabilitiesQuery, GetExecutionCapabilitiesQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetExecutionCapabilitiesQuery, GetExecutionCapabilitiesQueryVariables>(GetExecutionCapabilitiesDocument, options);
        }
export function useGetExecutionCapabilitiesSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetExecutionCapabilitiesQuery, GetExecutionCapabilitiesQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetExecutionCapabilitiesQuery, GetExecutionCapabilitiesQueryVariables>(GetExecutionCapabilitiesDocument, options);
        }
export type GetExecutionCapabilitiesQueryHookResult = ReturnType<typeof useGetExecutionCapabilitiesQuery>;
export type GetExecutionCapabilitiesLazyQueryHookResult = ReturnType<typeof useGetExecutionCapabilitiesLazyQuery>;
export type GetExecutionCapabilitiesSuspenseQueryHookResult = ReturnType<typeof useGetExecutionCapabilitiesSuspenseQuery>;
export type GetExecutionCapabilitiesQueryResult = Apollo.QueryResult<GetExecutionCapabilitiesQuery, GetExecutionCapabilitiesQueryVariables>;
export const GetExecutionHistoryDocument = gql`
    query GetExecutionHistory($diagram_id: ID, $limit: Int, $include_metrics: Boolean) {
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

/**
 * __useGetExecutionHistoryQuery__
 *
 * To run a query within a React component, call `useGetExecutionHistoryQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetExecutionHistoryQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetExecutionHistoryQuery({
 *   variables: {
 *      diagram_id: // value for 'diagram_id'
 *      limit: // value for 'limit'
 *      include_metrics: // value for 'include_metrics'
 *   },
 * });
 */
export function useGetExecutionHistoryQuery(baseOptions?: Apollo.QueryHookOptions<GetExecutionHistoryQuery, GetExecutionHistoryQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetExecutionHistoryQuery, GetExecutionHistoryQueryVariables>(GetExecutionHistoryDocument, options);
      }
export function useGetExecutionHistoryLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetExecutionHistoryQuery, GetExecutionHistoryQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetExecutionHistoryQuery, GetExecutionHistoryQueryVariables>(GetExecutionHistoryDocument, options);
        }
export function useGetExecutionHistorySuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetExecutionHistoryQuery, GetExecutionHistoryQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetExecutionHistoryQuery, GetExecutionHistoryQueryVariables>(GetExecutionHistoryDocument, options);
        }
export type GetExecutionHistoryQueryHookResult = ReturnType<typeof useGetExecutionHistoryQuery>;
export type GetExecutionHistoryLazyQueryHookResult = ReturnType<typeof useGetExecutionHistoryLazyQuery>;
export type GetExecutionHistorySuspenseQueryHookResult = ReturnType<typeof useGetExecutionHistorySuspenseQuery>;
export type GetExecutionHistoryQueryResult = Apollo.QueryResult<GetExecutionHistoryQuery, GetExecutionHistoryQueryVariables>;
export const GetExecutionMetricsDocument = gql`
    query GetExecutionMetrics($execution_id: ID!) {
  execution_metrics(execution_id: $execution_id)
}
    `;

/**
 * __useGetExecutionMetricsQuery__
 *
 * To run a query within a React component, call `useGetExecutionMetricsQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetExecutionMetricsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetExecutionMetricsQuery({
 *   variables: {
 *      execution_id: // value for 'execution_id'
 *   },
 * });
 */
export function useGetExecutionMetricsQuery(baseOptions: Apollo.QueryHookOptions<GetExecutionMetricsQuery, GetExecutionMetricsQueryVariables> & ({ variables: GetExecutionMetricsQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetExecutionMetricsQuery, GetExecutionMetricsQueryVariables>(GetExecutionMetricsDocument, options);
      }
export function useGetExecutionMetricsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetExecutionMetricsQuery, GetExecutionMetricsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetExecutionMetricsQuery, GetExecutionMetricsQueryVariables>(GetExecutionMetricsDocument, options);
        }
export function useGetExecutionMetricsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetExecutionMetricsQuery, GetExecutionMetricsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetExecutionMetricsQuery, GetExecutionMetricsQueryVariables>(GetExecutionMetricsDocument, options);
        }
export type GetExecutionMetricsQueryHookResult = ReturnType<typeof useGetExecutionMetricsQuery>;
export type GetExecutionMetricsLazyQueryHookResult = ReturnType<typeof useGetExecutionMetricsLazyQuery>;
export type GetExecutionMetricsSuspenseQueryHookResult = ReturnType<typeof useGetExecutionMetricsSuspenseQuery>;
export type GetExecutionMetricsQueryResult = Apollo.QueryResult<GetExecutionMetricsQuery, GetExecutionMetricsQueryVariables>;
export const GetExecutionOrderDocument = gql`
    query GetExecutionOrder($execution_id: ID!) {
  execution_order(execution_id: $execution_id)
}
    `;

/**
 * __useGetExecutionOrderQuery__
 *
 * To run a query within a React component, call `useGetExecutionOrderQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetExecutionOrderQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetExecutionOrderQuery({
 *   variables: {
 *      execution_id: // value for 'execution_id'
 *   },
 * });
 */
export function useGetExecutionOrderQuery(baseOptions: Apollo.QueryHookOptions<GetExecutionOrderQuery, GetExecutionOrderQueryVariables> & ({ variables: GetExecutionOrderQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetExecutionOrderQuery, GetExecutionOrderQueryVariables>(GetExecutionOrderDocument, options);
      }
export function useGetExecutionOrderLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetExecutionOrderQuery, GetExecutionOrderQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetExecutionOrderQuery, GetExecutionOrderQueryVariables>(GetExecutionOrderDocument, options);
        }
export function useGetExecutionOrderSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetExecutionOrderQuery, GetExecutionOrderQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetExecutionOrderQuery, GetExecutionOrderQueryVariables>(GetExecutionOrderDocument, options);
        }
export type GetExecutionOrderQueryHookResult = ReturnType<typeof useGetExecutionOrderQuery>;
export type GetExecutionOrderLazyQueryHookResult = ReturnType<typeof useGetExecutionOrderLazyQuery>;
export type GetExecutionOrderSuspenseQueryHookResult = ReturnType<typeof useGetExecutionOrderSuspenseQuery>;
export type GetExecutionOrderQueryResult = Apollo.QueryResult<GetExecutionOrderQuery, GetExecutionOrderQueryVariables>;
export const GetPersonDocument = gql`
    query GetPerson($id: ID!) {
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
export const GetSupportedFormatsDocument = gql`
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
export const HealthCheckDocument = gql`
    query HealthCheck {
  health
}
    `;

/**
 * __useHealthCheckQuery__
 *
 * To run a query within a React component, call `useHealthCheckQuery` and pass it any options that fit your needs.
 * When your component renders, `useHealthCheckQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useHealthCheckQuery({
 *   variables: {
 *   },
 * });
 */
export function useHealthCheckQuery(baseOptions?: Apollo.QueryHookOptions<HealthCheckQuery, HealthCheckQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<HealthCheckQuery, HealthCheckQueryVariables>(HealthCheckDocument, options);
      }
export function useHealthCheckLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<HealthCheckQuery, HealthCheckQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<HealthCheckQuery, HealthCheckQueryVariables>(HealthCheckDocument, options);
        }
export function useHealthCheckSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<HealthCheckQuery, HealthCheckQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<HealthCheckQuery, HealthCheckQueryVariables>(HealthCheckDocument, options);
        }
export type HealthCheckQueryHookResult = ReturnType<typeof useHealthCheckQuery>;
export type HealthCheckLazyQueryHookResult = ReturnType<typeof useHealthCheckLazyQuery>;
export type HealthCheckSuspenseQueryHookResult = ReturnType<typeof useHealthCheckSuspenseQuery>;
export type HealthCheckQueryResult = Apollo.QueryResult<HealthCheckQuery, HealthCheckQueryVariables>;
export const ListConversationsDocument = gql`
    query ListConversations($person_id: ID, $execution_id: ID, $search: String, $show_forgotten: Boolean, $limit: Int, $offset: Int, $since: DateTime) {
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
 * __useListConversationsQuery__
 *
 * To run a query within a React component, call `useListConversationsQuery` and pass it any options that fit your needs.
 * When your component renders, `useListConversationsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useListConversationsQuery({
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
export function useListConversationsQuery(baseOptions?: Apollo.QueryHookOptions<ListConversationsQuery, ListConversationsQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ListConversationsQuery, ListConversationsQueryVariables>(ListConversationsDocument, options);
      }
export function useListConversationsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ListConversationsQuery, ListConversationsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ListConversationsQuery, ListConversationsQueryVariables>(ListConversationsDocument, options);
        }
export function useListConversationsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ListConversationsQuery, ListConversationsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ListConversationsQuery, ListConversationsQueryVariables>(ListConversationsDocument, options);
        }
export type ListConversationsQueryHookResult = ReturnType<typeof useListConversationsQuery>;
export type ListConversationsLazyQueryHookResult = ReturnType<typeof useListConversationsLazyQuery>;
export type ListConversationsSuspenseQueryHookResult = ReturnType<typeof useListConversationsSuspenseQuery>;
export type ListConversationsQueryResult = Apollo.QueryResult<ListConversationsQuery, ListConversationsQueryVariables>;
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
export const ListExecutionsDocument = gql`
    query ListExecutions($filter: ExecutionFilterInput, $limit: Int, $offset: Int) {
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
export const ListPersonsDocument = gql`
    query ListPersons($limit: Int) {
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

/**
 * __useListPersonsQuery__
 *
 * To run a query within a React component, call `useListPersonsQuery` and pass it any options that fit your needs.
 * When your component renders, `useListPersonsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useListPersonsQuery({
 *   variables: {
 *      limit: // value for 'limit'
 *   },
 * });
 */
export function useListPersonsQuery(baseOptions?: Apollo.QueryHookOptions<ListPersonsQuery, ListPersonsQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ListPersonsQuery, ListPersonsQueryVariables>(ListPersonsDocument, options);
      }
export function useListPersonsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ListPersonsQuery, ListPersonsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ListPersonsQuery, ListPersonsQueryVariables>(ListPersonsDocument, options);
        }
export function useListPersonsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ListPersonsQuery, ListPersonsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ListPersonsQuery, ListPersonsQueryVariables>(ListPersonsDocument, options);
        }
export type ListPersonsQueryHookResult = ReturnType<typeof useListPersonsQuery>;
export type ListPersonsLazyQueryHookResult = ReturnType<typeof useListPersonsLazyQuery>;
export type ListPersonsSuspenseQueryHookResult = ReturnType<typeof useListPersonsSuspenseQuery>;
export type ListPersonsQueryResult = Apollo.QueryResult<ListPersonsQuery, ListPersonsQueryVariables>;
export const ListPromptFilesDocument = gql`
    query ListPromptFiles {
  prompt_files
}
    `;

/**
 * __useListPromptFilesQuery__
 *
 * To run a query within a React component, call `useListPromptFilesQuery` and pass it any options that fit your needs.
 * When your component renders, `useListPromptFilesQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useListPromptFilesQuery({
 *   variables: {
 *   },
 * });
 */
export function useListPromptFilesQuery(baseOptions?: Apollo.QueryHookOptions<ListPromptFilesQuery, ListPromptFilesQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ListPromptFilesQuery, ListPromptFilesQueryVariables>(ListPromptFilesDocument, options);
      }
export function useListPromptFilesLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ListPromptFilesQuery, ListPromptFilesQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ListPromptFilesQuery, ListPromptFilesQueryVariables>(ListPromptFilesDocument, options);
        }
export function useListPromptFilesSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ListPromptFilesQuery, ListPromptFilesQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ListPromptFilesQuery, ListPromptFilesQueryVariables>(ListPromptFilesDocument, options);
        }
export type ListPromptFilesQueryHookResult = ReturnType<typeof useListPromptFilesQuery>;
export type ListPromptFilesLazyQueryHookResult = ReturnType<typeof useListPromptFilesLazyQuery>;
export type ListPromptFilesSuspenseQueryHookResult = ReturnType<typeof useListPromptFilesSuspenseQuery>;
export type ListPromptFilesQueryResult = Apollo.QueryResult<ListPromptFilesQuery, ListPromptFilesQueryVariables>;
export const ExecutionUpdatesDocument = gql`
    subscription ExecutionUpdates($execution_id: ID!) {
  execution_updates(execution_id: $execution_id) {
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
 *      execution_id: // value for 'execution_id'
 *   },
 * });
 */
export function useExecutionUpdatesSubscription(baseOptions: Apollo.SubscriptionHookOptions<ExecutionUpdatesSubscription, ExecutionUpdatesSubscriptionVariables> & ({ variables: ExecutionUpdatesSubscriptionVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useSubscription<ExecutionUpdatesSubscription, ExecutionUpdatesSubscriptionVariables>(ExecutionUpdatesDocument, options);
      }
export type ExecutionUpdatesSubscriptionHookResult = ReturnType<typeof useExecutionUpdatesSubscription>;
export type ExecutionUpdatesSubscriptionResult = Apollo.SubscriptionResult<ExecutionUpdatesSubscription>;
export const ProvidersDocument = gql`
    query Providers {
  providers {
    name
    metadata {
      description
    }
  }
}
    `;

/**
 * __useProvidersQuery__
 *
 * To run a query within a React component, call `useProvidersQuery` and pass it any options that fit your needs.
 * When your component renders, `useProvidersQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useProvidersQuery({
 *   variables: {
 *   },
 * });
 */
export function useProvidersQuery(baseOptions?: Apollo.QueryHookOptions<ProvidersQuery, ProvidersQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ProvidersQuery, ProvidersQueryVariables>(ProvidersDocument, options);
      }
export function useProvidersLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ProvidersQuery, ProvidersQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ProvidersQuery, ProvidersQueryVariables>(ProvidersDocument, options);
        }
export function useProvidersSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ProvidersQuery, ProvidersQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ProvidersQuery, ProvidersQueryVariables>(ProvidersDocument, options);
        }
export type ProvidersQueryHookResult = ReturnType<typeof useProvidersQuery>;
export type ProvidersLazyQueryHookResult = ReturnType<typeof useProvidersLazyQuery>;
export type ProvidersSuspenseQueryHookResult = ReturnType<typeof useProvidersSuspenseQuery>;
export type ProvidersQueryResult = Apollo.QueryResult<ProvidersQuery, ProvidersQueryVariables>;
export const ProviderOpsDocument = gql`
    query ProviderOps($provider: String!) {
  provider_operations(provider: $provider) {
    name
    description
  }
}
    `;

/**
 * __useProviderOpsQuery__
 *
 * To run a query within a React component, call `useProviderOpsQuery` and pass it any options that fit your needs.
 * When your component renders, `useProviderOpsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useProviderOpsQuery({
 *   variables: {
 *      provider: // value for 'provider'
 *   },
 * });
 */
export function useProviderOpsQuery(baseOptions: Apollo.QueryHookOptions<ProviderOpsQuery, ProviderOpsQueryVariables> & ({ variables: ProviderOpsQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ProviderOpsQuery, ProviderOpsQueryVariables>(ProviderOpsDocument, options);
      }
export function useProviderOpsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ProviderOpsQuery, ProviderOpsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ProviderOpsQuery, ProviderOpsQueryVariables>(ProviderOpsDocument, options);
        }
export function useProviderOpsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ProviderOpsQuery, ProviderOpsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ProviderOpsQuery, ProviderOpsQueryVariables>(ProviderOpsDocument, options);
        }
export type ProviderOpsQueryHookResult = ReturnType<typeof useProviderOpsQuery>;
export type ProviderOpsLazyQueryHookResult = ReturnType<typeof useProviderOpsLazyQuery>;
export type ProviderOpsSuspenseQueryHookResult = ReturnType<typeof useProviderOpsSuspenseQuery>;
export type ProviderOpsQueryResult = Apollo.QueryResult<ProviderOpsQuery, ProviderOpsQueryVariables>;
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
export const GetExecutionStateDocument = gql`
    query GetExecutionState($id: ID!) {
  execution(id: $id) {
    id
    status
    started_at
    ended_at
    node_states
    node_outputs
  }
}
    `;

/**
 * __useGetExecutionStateQuery__
 *
 * To run a query within a React component, call `useGetExecutionStateQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetExecutionStateQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetExecutionStateQuery({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useGetExecutionStateQuery(baseOptions: Apollo.QueryHookOptions<GetExecutionStateQuery, GetExecutionStateQueryVariables> & ({ variables: GetExecutionStateQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetExecutionStateQuery, GetExecutionStateQueryVariables>(GetExecutionStateDocument, options);
      }
export function useGetExecutionStateLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetExecutionStateQuery, GetExecutionStateQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetExecutionStateQuery, GetExecutionStateQueryVariables>(GetExecutionStateDocument, options);
        }
export function useGetExecutionStateSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetExecutionStateQuery, GetExecutionStateQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetExecutionStateQuery, GetExecutionStateQueryVariables>(GetExecutionStateDocument, options);
        }
export type GetExecutionStateQueryHookResult = ReturnType<typeof useGetExecutionStateQuery>;
export type GetExecutionStateLazyQueryHookResult = ReturnType<typeof useGetExecutionStateLazyQuery>;
export type GetExecutionStateSuspenseQueryHookResult = ReturnType<typeof useGetExecutionStateSuspenseQuery>;
export type GetExecutionStateQueryResult = Apollo.QueryResult<GetExecutionStateQuery, GetExecutionStateQueryVariables>;
export const GetProvidersDocument = gql`
    query GetProviders {
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
}
    `;

/**
 * __useGetProvidersQuery__
 *
 * To run a query within a React component, call `useGetProvidersQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetProvidersQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetProvidersQuery({
 *   variables: {
 *   },
 * });
 */
export function useGetProvidersQuery(baseOptions?: Apollo.QueryHookOptions<GetProvidersQuery, GetProvidersQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetProvidersQuery, GetProvidersQueryVariables>(GetProvidersDocument, options);
      }
export function useGetProvidersLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetProvidersQuery, GetProvidersQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetProvidersQuery, GetProvidersQueryVariables>(GetProvidersDocument, options);
        }
export function useGetProvidersSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetProvidersQuery, GetProvidersQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetProvidersQuery, GetProvidersQueryVariables>(GetProvidersDocument, options);
        }
export type GetProvidersQueryHookResult = ReturnType<typeof useGetProvidersQuery>;
export type GetProvidersLazyQueryHookResult = ReturnType<typeof useGetProvidersLazyQuery>;
export type GetProvidersSuspenseQueryHookResult = ReturnType<typeof useGetProvidersSuspenseQuery>;
export type GetProvidersQueryResult = Apollo.QueryResult<GetProvidersQuery, GetProvidersQueryVariables>;
export const GetProviderOperationsDocument = gql`
    query GetProviderOperations($provider: String!) {
  provider_operations(provider: $provider) {
    name
    method
    path
    description
    required_scopes
    has_pagination
    timeout_override
  }
}
    `;

/**
 * __useGetProviderOperationsQuery__
 *
 * To run a query within a React component, call `useGetProviderOperationsQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetProviderOperationsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetProviderOperationsQuery({
 *   variables: {
 *      provider: // value for 'provider'
 *   },
 * });
 */
export function useGetProviderOperationsQuery(baseOptions: Apollo.QueryHookOptions<GetProviderOperationsQuery, GetProviderOperationsQueryVariables> & ({ variables: GetProviderOperationsQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetProviderOperationsQuery, GetProviderOperationsQueryVariables>(GetProviderOperationsDocument, options);
      }
export function useGetProviderOperationsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetProviderOperationsQuery, GetProviderOperationsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetProviderOperationsQuery, GetProviderOperationsQueryVariables>(GetProviderOperationsDocument, options);
        }
export function useGetProviderOperationsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetProviderOperationsQuery, GetProviderOperationsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetProviderOperationsQuery, GetProviderOperationsQueryVariables>(GetProviderOperationsDocument, options);
        }
export type GetProviderOperationsQueryHookResult = ReturnType<typeof useGetProviderOperationsQuery>;
export type GetProviderOperationsLazyQueryHookResult = ReturnType<typeof useGetProviderOperationsLazyQuery>;
export type GetProviderOperationsSuspenseQueryHookResult = ReturnType<typeof useGetProviderOperationsSuspenseQuery>;
export type GetProviderOperationsQueryResult = Apollo.QueryResult<GetProviderOperationsQuery, GetProviderOperationsQueryVariables>;
export const GetOperationSchemaDocument = gql`
    query GetOperationSchema($provider: String!, $operation: String!) {
  operation_schema(provider: $provider, operation: $operation) {
    operation
    method
    path
    description
    request_body
    query_params
    response
  }
}
    `;

/**
 * __useGetOperationSchemaQuery__
 *
 * To run a query within a React component, call `useGetOperationSchemaQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetOperationSchemaQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetOperationSchemaQuery({
 *   variables: {
 *      provider: // value for 'provider'
 *      operation: // value for 'operation'
 *   },
 * });
 */
export function useGetOperationSchemaQuery(baseOptions: Apollo.QueryHookOptions<GetOperationSchemaQuery, GetOperationSchemaQueryVariables> & ({ variables: GetOperationSchemaQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetOperationSchemaQuery, GetOperationSchemaQueryVariables>(GetOperationSchemaDocument, options);
      }
export function useGetOperationSchemaLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetOperationSchemaQuery, GetOperationSchemaQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetOperationSchemaQuery, GetOperationSchemaQueryVariables>(GetOperationSchemaDocument, options);
        }
export function useGetOperationSchemaSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetOperationSchemaQuery, GetOperationSchemaQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetOperationSchemaQuery, GetOperationSchemaQueryVariables>(GetOperationSchemaDocument, options);
        }
export type GetOperationSchemaQueryHookResult = ReturnType<typeof useGetOperationSchemaQuery>;
export type GetOperationSchemaLazyQueryHookResult = ReturnType<typeof useGetOperationSchemaLazyQuery>;
export type GetOperationSchemaSuspenseQueryHookResult = ReturnType<typeof useGetOperationSchemaSuspenseQuery>;
export type GetOperationSchemaQueryResult = Apollo.QueryResult<GetOperationSchemaQuery, GetOperationSchemaQueryVariables>;
export const ListRecentExecutionsDocument = gql`
    query ListRecentExecutions($limit: Int) {
  executions(limit: $limit) {
    id
    diagram_id
    status
    started_at
    ended_at
    error
  }
}
    `;

/**
 * __useListRecentExecutionsQuery__
 *
 * To run a query within a React component, call `useListRecentExecutionsQuery` and pass it any options that fit your needs.
 * When your component renders, `useListRecentExecutionsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useListRecentExecutionsQuery({
 *   variables: {
 *      limit: // value for 'limit'
 *   },
 * });
 */
export function useListRecentExecutionsQuery(baseOptions?: Apollo.QueryHookOptions<ListRecentExecutionsQuery, ListRecentExecutionsQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ListRecentExecutionsQuery, ListRecentExecutionsQueryVariables>(ListRecentExecutionsDocument, options);
      }
export function useListRecentExecutionsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ListRecentExecutionsQuery, ListRecentExecutionsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ListRecentExecutionsQuery, ListRecentExecutionsQueryVariables>(ListRecentExecutionsDocument, options);
        }
export function useListRecentExecutionsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ListRecentExecutionsQuery, ListRecentExecutionsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ListRecentExecutionsQuery, ListRecentExecutionsQueryVariables>(ListRecentExecutionsDocument, options);
        }
export type ListRecentExecutionsQueryHookResult = ReturnType<typeof useListRecentExecutionsQuery>;
export type ListRecentExecutionsLazyQueryHookResult = ReturnType<typeof useListRecentExecutionsLazyQuery>;
export type ListRecentExecutionsSuspenseQueryHookResult = ReturnType<typeof useListRecentExecutionsSuspenseQuery>;
export type ListRecentExecutionsQueryResult = Apollo.QueryResult<ListRecentExecutionsQuery, ListRecentExecutionsQueryVariables>;
export const ListActiveExecutionsDocument = gql`
    query ListActiveExecutions($filter: ExecutionFilterInput, $limit: Int) {
  executions(filter: $filter, limit: $limit) {
    id
    status
    diagram_id
    started_at
    ended_at
  }
}
    `;

/**
 * __useListActiveExecutionsQuery__
 *
 * To run a query within a React component, call `useListActiveExecutionsQuery` and pass it any options that fit your needs.
 * When your component renders, `useListActiveExecutionsQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useListActiveExecutionsQuery({
 *   variables: {
 *      filter: // value for 'filter'
 *      limit: // value for 'limit'
 *   },
 * });
 */
export function useListActiveExecutionsQuery(baseOptions?: Apollo.QueryHookOptions<ListActiveExecutionsQuery, ListActiveExecutionsQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<ListActiveExecutionsQuery, ListActiveExecutionsQueryVariables>(ListActiveExecutionsDocument, options);
      }
export function useListActiveExecutionsLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<ListActiveExecutionsQuery, ListActiveExecutionsQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<ListActiveExecutionsQuery, ListActiveExecutionsQueryVariables>(ListActiveExecutionsDocument, options);
        }
export function useListActiveExecutionsSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<ListActiveExecutionsQuery, ListActiveExecutionsQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<ListActiveExecutionsQuery, ListActiveExecutionsQueryVariables>(ListActiveExecutionsDocument, options);
        }
export type ListActiveExecutionsQueryHookResult = ReturnType<typeof useListActiveExecutionsQuery>;
export type ListActiveExecutionsLazyQueryHookResult = ReturnType<typeof useListActiveExecutionsLazyQuery>;
export type ListActiveExecutionsSuspenseQueryHookResult = ReturnType<typeof useListActiveExecutionsSuspenseQuery>;
export type ListActiveExecutionsQueryResult = Apollo.QueryResult<ListActiveExecutionsQuery, ListActiveExecutionsQueryVariables>;