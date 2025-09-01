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

export type ProvidersQueryVariables = Exact<{ [key: string]: never; }>;


export type ProvidersQuery = { __typename?: 'Query', providers: Array<{ __typename?: 'ProviderType', name: string, metadata: { __typename?: 'ProviderMetadataType', description?: string | null } }> };

export type ProviderOpsQueryVariables = Exact<{
  provider: Scalars['String']['input'];
}>;


export type ProviderOpsQuery = { __typename?: 'Query', provider_operations: Array<{ __typename?: 'OperationType', name: string, description?: string | null }> };

export type ActiveCliSessionQueryVariables = Exact<{ [key: string]: never; }>;


export type ActiveCliSessionQuery = { __typename?: 'Query', active_cli_session?: { __typename?: 'CliSession', session_id: string, execution_id: string, diagram_name: string, diagram_format: string, started_at: any, is_active: boolean, diagram_data?: string | null } | null };

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