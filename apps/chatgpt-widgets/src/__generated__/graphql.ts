import type { NodeType } from '@dipeo/models';
import type { HandleDirection } from '@dipeo/models';
import type { HandleLabel } from '@dipeo/models';
import type { DataType } from '@dipeo/models';
import type { LLMService } from '@dipeo/models';
import type { DiagramFormat as DiagramFormatGraphQL } from '@dipeo/models';
import type { Status } from '@dipeo/models';
import type { ApiKeyID } from '@dipeo/models';
import type { ArrowID } from '@dipeo/models';
import type { DiagramID } from '@dipeo/models';
import type { ExecutionID } from '@dipeo/models';
import type { HandleID } from '@dipeo/models';
import type { NodeID } from '@dipeo/models';
import type { PersonID } from '@dipeo/models';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /** Branded scalar type for ApiKeyID */
  ApiKeyID: { input: ApiKeyID; output: ApiKeyID; }
  /** Branded scalar type for ArrowID */
  ArrowID: { input: ArrowID; output: ArrowID; }
  /** Date with time (isoformat) */
  DateTime: { input: string; output: string; }
  /** Branded scalar type for DiagramID */
  DiagramID: { input: DiagramID; output: DiagramID; }
  /** Branded scalar type for ExecutionID */
  ExecutionID: { input: ExecutionID; output: ExecutionID; }
  /** Branded scalar type for HandleID */
  HandleID: { input: HandleID; output: HandleID; }
  /** Branded scalar type for HookID */
  HookID: { input: any; output: any; }
  /** The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf). */
  JSON: { input: Record<string, unknown>; output: Record<string, unknown>; }
  /** Branded scalar type for NodeID */
  NodeID: { input: NodeID; output: NodeID; }
  /** Branded scalar type for PersonID */
  PersonID: { input: PersonID; output: PersonID; }
  /** Branded scalar type for TaskID */
  TaskID: { input: any; output: any; }
  Upload: { input: any; output: any; }
};

export enum APIServiceType {
  ANTHROPIC = 'ANTHROPIC',
  CLAUDE_CODE = 'CLAUDE_CODE',
  CLAUDE_CODE_CUSTOM = 'CLAUDE_CODE_CUSTOM',
  GEMINI = 'GEMINI',
  GOOGLE = 'GOOGLE',
  OLLAMA = 'OLLAMA',
  OPENAI = 'OPENAI'
}

export type ApiKeyResult = {
  __typename?: 'ApiKeyResult';
  data?: Maybe<DomainApiKeyType>;
  envelope?: Maybe<Scalars['JSON']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  error_type?: Maybe<Scalars['String']['output']>;
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

export type CliSessionResult = {
  __typename?: 'CliSessionResult';
  data?: Maybe<Scalars['JSON']['output']>;
  envelope?: Maybe<Scalars['JSON']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  error_type?: Maybe<Scalars['String']['output']>;
  execution_id?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  session_id?: Maybe<Scalars['String']['output']>;
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
  tags?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type CreateNodeInput = {
  data: Scalars['JSON']['input'];
  position: Vec2Input;
  type: NodeType;
};

export type CreatePersonInput = {
  label: Scalars['String']['input'];
  llm_config: PersonLLMConfigInput;
  type?: InputMaybe<Scalars['String']['input']>;
};

export { DataType };

export type DeleteResult = {
  __typename?: 'DeleteResult';
  data?: Maybe<Scalars['JSON']['output']>;
  deleted_count?: Maybe<Scalars['Int']['output']>;
  deleted_id?: Maybe<Scalars['String']['output']>;
  envelope?: Maybe<Scalars['JSON']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  error_type?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type DiagramFilterInput = {
  author?: InputMaybe<Scalars['String']['input']>;
  created_after?: InputMaybe<Scalars['DateTime']['input']>;
  created_before?: InputMaybe<Scalars['DateTime']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  tags?: InputMaybe<Scalars['String']['input']>;
};

export { DiagramFormatGraphQL };

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
  data?: Maybe<DomainDiagramType>;
  envelope?: Maybe<Scalars['JSON']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  error_type?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type DomainApiKeyType = {
  __typename?: 'DomainApiKeyType';
  id: Scalars['ID']['output'];
  key?: Maybe<Scalars['String']['output']>;
  label: Scalars['String']['output'];
  service: APIServiceType;
};

export type DomainArrowType = {
  __typename?: 'DomainArrowType';
  content_type?: Maybe<ContentType>;
  data?: Maybe<Scalars['JSON']['output']>;
  execution_priority?: Maybe<Scalars['Float']['output']>;
  id: Scalars['ID']['output'];
  label?: Maybe<Scalars['String']['output']>;
  source: Scalars['ID']['output'];
  target: Scalars['ID']['output'];
};

export type DomainDiagramType = {
  __typename?: 'DomainDiagramType';
  arrows: Array<DomainArrowType>;
  handles: Array<DomainHandleType>;
  metadata?: Maybe<DiagramMetadataType>;
  nodes: Array<DomainNodeType>;
  persons: Array<DomainPersonType>;
};

export type DomainHandleType = {
  __typename?: 'DomainHandleType';
  data_type: DataType;
  direction: HandleDirection;
  id: Scalars['ID']['output'];
  label: HandleLabel;
  node_id: Scalars['ID']['output'];
  position?: Maybe<Scalars['String']['output']>;
};

export type DomainNodeType = {
  __typename?: 'DomainNodeType';
  data: Scalars['JSON']['output'];
  id: Scalars['ID']['output'];
  position: Vec2Type;
  type: NodeType;
};

export type DomainPersonType = {
  __typename?: 'DomainPersonType';
  id: Scalars['ID']['output'];
  label: Scalars['String']['output'];
  llm_config: PersonLLMConfigType;
  type: Scalars['String']['output'];
};

export enum EventType {
  EXECUTION_COMPLETED = 'EXECUTION_COMPLETED',
  EXECUTION_ERROR = 'EXECUTION_ERROR',
  EXECUTION_LOG = 'EXECUTION_LOG',
  EXECUTION_STARTED = 'EXECUTION_STARTED',
  INTERACTIVE_PROMPT = 'INTERACTIVE_PROMPT',
  INTERACTIVE_RESPONSE = 'INTERACTIVE_RESPONSE',
  NODE_COMPLETED = 'NODE_COMPLETED',
  NODE_ERROR = 'NODE_ERROR',
  NODE_OUTPUT = 'NODE_OUTPUT',
  NODE_STARTED = 'NODE_STARTED'
}

export type ExecuteDiagramInput = {
  debug_mode?: InputMaybe<Scalars['Boolean']['input']>;
  diagram_data?: InputMaybe<Scalars['JSON']['input']>;
  diagram_id?: InputMaybe<Scalars['ID']['input']>;
  max_iterations?: InputMaybe<Scalars['Int']['input']>;
  timeout_seconds?: InputMaybe<Scalars['Int']['input']>;
  use_unified_monitoring?: InputMaybe<Scalars['Boolean']['input']>;
  variables?: InputMaybe<Scalars['JSON']['input']>;
};

export type ExecuteIntegrationInput = {
  api_key_id?: InputMaybe<Scalars['ID']['input']>;
  config: Scalars['JSON']['input'];
  operation: Scalars['String']['input'];
  provider: Scalars['String']['input'];
  resource_id?: InputMaybe<Scalars['String']['input']>;
  timeout?: InputMaybe<Scalars['Int']['input']>;
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
  data?: Maybe<ExecutionStateType>;
  envelope?: Maybe<Scalars['JSON']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  error_type?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type ExecutionStateType = {
  __typename?: 'ExecutionStateType';
  diagram_id?: Maybe<Scalars['ID']['output']>;
  ended_at?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  exec_counts: Scalars['JSON']['output'];
  executed_nodes: Array<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  is_active?: Maybe<Scalars['Boolean']['output']>;
  llm_usage?: Maybe<LLMUsageType>;
  metrics?: Maybe<Scalars['JSON']['output']>;
  node_outputs: Scalars['JSON']['output'];
  node_states: Scalars['JSON']['output'];
  started_at?: Maybe<Scalars['String']['output']>;
  status: Status;
  variables?: Maybe<Scalars['JSON']['output']>;
};

export type ExecutionUpdateType = {
  __typename?: 'ExecutionUpdateType';
  data?: Maybe<Scalars['JSON']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  execution_id: Scalars['ID']['output'];
  node_id?: Maybe<Scalars['ID']['output']>;
  node_type?: Maybe<Scalars['String']['output']>;
  result?: Maybe<Scalars['JSON']['output']>;
  status?: Maybe<Status>;
  timestamp?: Maybe<Scalars['String']['output']>;
  tokens?: Maybe<Scalars['Float']['output']>;
  total_tokens?: Maybe<Scalars['Float']['output']>;
  type: EventType;
};

export type FormatConversionResult = {
  __typename?: 'FormatConversionResult';
  data?: Maybe<Scalars['String']['output']>;
  envelope?: Maybe<Scalars['JSON']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  error_type?: Maybe<Scalars['String']['output']>;
  format?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  original_format?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export { HandleDirection };

export { HandleLabel };

export type IntegrationTestResultType = {
  __typename?: 'IntegrationTestResultType';
  error?: Maybe<Scalars['String']['output']>;
  operation: Scalars['String']['output'];
  provider: Scalars['String']['output'];
  response_preview?: Maybe<Scalars['JSON']['output']>;
  response_time_ms?: Maybe<Scalars['Float']['output']>;
  status_code?: Maybe<Scalars['Float']['output']>;
  success: Scalars['Boolean']['output'];
};

export type InteractiveResponseInput = {
  execution_id: Scalars['ID']['input'];
  metadata?: InputMaybe<Scalars['JSON']['input']>;
  node_id: Scalars['ID']['input'];
  response: Scalars['String']['input'];
};

export { LLMService };

export type LLMUsageType = {
  __typename?: 'LLMUsageType';
  cached?: Maybe<Scalars['Float']['output']>;
  input: Scalars['Float']['output'];
  output: Scalars['Float']['output'];
  total?: Maybe<Scalars['Float']['output']>;
};

export type Mutation = {
  __typename?: 'Mutation';
  controlExecution: ExecutionResult;
  convertDiagramFormat: FormatConversionResult;
  createApiKey: ApiKeyResult;
  createDiagram: DiagramResult;
  createNode: NodeResult;
  createPerson: PersonResult;
  deleteApiKey: DeleteResult;
  deleteDiagram: DeleteResult;
  deleteNode: DeleteResult;
  deletePerson: DeleteResult;
  executeDiagram: ExecutionResult;
  executeIntegration: Scalars['JSON']['output'];
  registerCliSession: CliSessionResult;
  reloadProvider: Scalars['JSON']['output'];
  sendInteractiveResponse: ExecutionResult;
  testApiKey: ApiKeyResult;
  testIntegration: IntegrationTestResultType;
  unregisterCliSession: CliSessionResult;
  updateNode: NodeResult;
  updateNodeState: ExecutionResult;
  updatePerson: PersonResult;
  uploadDiagram: Scalars['JSON']['output'];
  uploadFile: Scalars['JSON']['output'];
  validateDiagram: Scalars['JSON']['output'];
};


export type MutationcontrolExecutionArgs = {
  input: ExecutionControlInput;
};


export type MutationconvertDiagramFormatArgs = {
  content: Scalars['String']['input'];
  from_format: DiagramFormatGraphQL;
  to_format: DiagramFormatGraphQL;
};


export type MutationcreateApiKeyArgs = {
  input: CreateApiKeyInput;
};


export type MutationcreateDiagramArgs = {
  input: CreateDiagramInput;
};


export type MutationcreateNodeArgs = {
  diagram_id: Scalars['String']['input'];
  input: CreateNodeInput;
};


export type MutationcreatePersonArgs = {
  input: CreatePersonInput;
};


export type MutationdeleteApiKeyArgs = {
  api_key_id: Scalars['String']['input'];
};


export type MutationdeleteDiagramArgs = {
  diagram_id: Scalars['String']['input'];
};


export type MutationdeleteNodeArgs = {
  diagram_id: Scalars['String']['input'];
  node_id: Scalars['String']['input'];
};


export type MutationdeletePersonArgs = {
  person_id: Scalars['String']['input'];
};


export type MutationexecuteDiagramArgs = {
  input: ExecuteDiagramInput;
};


export type MutationexecuteIntegrationArgs = {
  input: ExecuteIntegrationInput;
};


export type MutationregisterCliSessionArgs = {
  input: RegisterCliSessionInput;
};


export type MutationreloadProviderArgs = {
  name: Scalars['String']['input'];
};


export type MutationsendInteractiveResponseArgs = {
  input: InteractiveResponseInput;
};


export type MutationtestApiKeyArgs = {
  api_key_id: Scalars['String']['input'];
};


export type MutationtestIntegrationArgs = {
  input: TestIntegrationInput;
};


export type MutationunregisterCliSessionArgs = {
  input: UnregisterCliSessionInput;
};


export type MutationupdateNodeArgs = {
  diagram_id: Scalars['String']['input'];
  input: UpdateNodeInput;
  node_id: Scalars['String']['input'];
};


export type MutationupdateNodeStateArgs = {
  input: UpdateNodeStateInput;
};


export type MutationupdatePersonArgs = {
  input: UpdatePersonInput;
  person_id: Scalars['String']['input'];
};


export type MutationuploadDiagramArgs = {
  file: Scalars['Upload']['input'];
  format: DiagramFormatGraphQL;
};


export type MutationuploadFileArgs = {
  file: Scalars['Upload']['input'];
  path?: InputMaybe<Scalars['String']['input']>;
};


export type MutationvalidateDiagramArgs = {
  content: Scalars['String']['input'];
  format: DiagramFormatGraphQL;
};

export type NodeResult = {
  __typename?: 'NodeResult';
  data?: Maybe<DomainNodeType>;
  envelope?: Maybe<Scalars['JSON']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  error_type?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
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
  api_key_id: Scalars['ID']['output'];
  model: Scalars['String']['output'];
  prompt_file?: Maybe<Scalars['String']['output']>;
  service: LLMService;
  system_prompt?: Maybe<Scalars['String']['output']>;
};

export type PersonResult = {
  __typename?: 'PersonResult';
  data?: Maybe<DomainPersonType>;
  envelope?: Maybe<Scalars['JSON']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  error_type?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
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
  providers: Scalars['JSON']['output'];
  total_operations: Scalars['Float']['output'];
  total_providers: Scalars['Float']['output'];
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
  getActiveCliSession: Scalars['JSON']['output'];
  getApiKey: DomainApiKeyType;
  getApiKeys: Scalars['JSON']['output'];
  getAvailableModels: Scalars['JSON']['output'];
  getDiagram: DomainDiagramType;
  getExecution?: Maybe<ExecutionStateType>;
  getExecutionCapabilities: Scalars['JSON']['output'];
  getExecutionHistory: Scalars['JSON']['output'];
  getExecutionMetrics: Scalars['JSON']['output'];
  getExecutionOrder: Scalars['JSON']['output'];
  getOperationSchema?: Maybe<OperationSchemaType>;
  getPerson: DomainPersonType;
  getPromptFile: Scalars['JSON']['output'];
  getProvider?: Maybe<ProviderType>;
  getProviderOperations: Scalars['JSON']['output'];
  getProviderStatistics: ProviderStatisticsType;
  getSupportedFormats: Scalars['JSON']['output'];
  getSystemInfo: Scalars['JSON']['output'];
  healthCheck: Scalars['JSON']['output'];
  listConversations: Array<Scalars['JSON']['output']>;
  listDiagrams: Array<DomainDiagramType>;
  listExecutions: Array<ExecutionStateType>;
  listPersons: Array<DomainPersonType>;
  listPromptFiles: Array<Scalars['JSON']['output']>;
  listProviders: Array<ProviderType>;
};


export type QuerygetApiKeyArgs = {
  api_key_id: Scalars['String']['input'];
};


export type QuerygetApiKeysArgs = {
  service?: InputMaybe<Scalars['String']['input']>;
};


export type QuerygetAvailableModelsArgs = {
  api_key_id: Scalars['String']['input'];
  service: Scalars['String']['input'];
};


export type QuerygetDiagramArgs = {
  diagram_id: Scalars['String']['input'];
};


export type QuerygetExecutionArgs = {
  execution_id: Scalars['String']['input'];
};


export type QuerygetExecutionHistoryArgs = {
  diagram_id?: InputMaybe<Scalars['String']['input']>;
  include_metrics?: InputMaybe<Scalars['Boolean']['input']>;
  limit?: InputMaybe<Scalars['Float']['input']>;
};


export type QuerygetExecutionMetricsArgs = {
  execution_id: Scalars['String']['input'];
};


export type QuerygetExecutionOrderArgs = {
  execution_id: Scalars['String']['input'];
};


export type QuerygetOperationSchemaArgs = {
  operation: Scalars['String']['input'];
  provider: Scalars['String']['input'];
};


export type QuerygetPersonArgs = {
  person_id: Scalars['String']['input'];
};


export type QuerygetPromptFileArgs = {
  filename: Scalars['String']['input'];
};


export type QuerygetProviderArgs = {
  name: Scalars['String']['input'];
};


export type QuerygetProviderOperationsArgs = {
  provider: Scalars['String']['input'];
};


export type QuerylistConversationsArgs = {
  execution_id?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Float']['input']>;
  offset?: InputMaybe<Scalars['Float']['input']>;
  person_id?: InputMaybe<Scalars['String']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  show_forgotten?: InputMaybe<Scalars['Boolean']['input']>;
  since?: InputMaybe<Scalars['String']['input']>;
};


export type QuerylistDiagramsArgs = {
  filter?: InputMaybe<DiagramFilterInput>;
  limit?: InputMaybe<Scalars['Float']['input']>;
  offset?: InputMaybe<Scalars['Float']['input']>;
};


export type QuerylistExecutionsArgs = {
  filter?: InputMaybe<ExecutionFilterInput>;
  limit?: InputMaybe<Scalars['Float']['input']>;
  offset?: InputMaybe<Scalars['Float']['input']>;
};


export type QuerylistPersonsArgs = {
  limit?: InputMaybe<Scalars['Float']['input']>;
};

export type RateLimitConfigType = {
  __typename?: 'RateLimitConfigType';
  algorithm: Scalars['String']['output'];
  capacity: Scalars['Float']['output'];
  refill_per_sec: Scalars['Float']['output'];
  window_size_sec?: Maybe<Scalars['Float']['output']>;
};

export type RegisterCliSessionInput = {
  diagram_data?: InputMaybe<Scalars['JSON']['input']>;
  diagram_format: DiagramFormatGraphQL;
  diagram_name: Scalars['String']['input'];
  execution_id: Scalars['ID']['input'];
};

export type RetryPolicyType = {
  __typename?: 'RetryPolicyType';
  base_delay_ms: Scalars['Float']['output'];
  max_delay_ms?: Maybe<Scalars['Float']['output']>;
  max_retries: Scalars['Float']['output'];
  retry_on_status: Array<Scalars['Float']['output']>;
  strategy: Scalars['String']['output'];
};

export { Status };

export type Subscription = {
  __typename?: 'Subscription';
  executionUpdates: ExecutionUpdateType;
};


export type SubscriptionexecutionUpdatesArgs = {
  execution_id: Scalars['String']['input'];
};

export type TestIntegrationInput = {
  api_key_id?: InputMaybe<Scalars['ID']['input']>;
  config_preview: Scalars['JSON']['input'];
  dry_run?: InputMaybe<Scalars['Boolean']['input']>;
  operation: Scalars['String']['input'];
  provider: Scalars['String']['input'];
};

export type UnregisterCliSessionInput = {
  execution_id: Scalars['ID']['input'];
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
  x: Scalars['Float']['output'];
  y: Scalars['Float']['output'];
};

export type GetExecutionQueryVariables = Exact<{
  executionId: Scalars['String']['input'];
}>;


export type GetExecutionQuery = { __typename?: 'Query', getExecution?: { __typename?: 'ExecutionStateType', id: string, status: Status, diagram_id?: string | null, started_at?: string | null, ended_at?: string | null, error?: string | null, metrics?: Record<string, unknown> | null, llm_usage?: { __typename?: 'LLMUsageType', input: number, output: number, cached?: number | null, total?: number | null } | null } | null };

export type ListExecutionsQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Float']['input']>;
}>;


export type ListExecutionsQuery = { __typename?: 'Query', listExecutions: Array<{ __typename?: 'ExecutionStateType', id: string, status: Status, diagram_id?: string | null, started_at?: string | null, ended_at?: string | null, error?: string | null }> };

export type ListDiagramsQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Float']['input']>;
}>;


export type ListDiagramsQuery = { __typename?: 'Query', listDiagrams: Array<{ __typename?: 'DomainDiagramType', metadata?: { __typename?: 'DiagramMetadataType', name?: string | null, description?: string | null, format?: string | null, created: string, modified: string } | null, nodes: Array<{ __typename?: 'DomainNodeType', id: string, type: NodeType, data: Record<string, unknown>, position: { __typename?: 'Vec2Type', x: number, y: number } }>, arrows: Array<{ __typename?: 'DomainArrowType', id: string, source: string, target: string, label?: string | null, content_type?: ContentType | null, data?: Record<string, unknown> | null }> }> };
