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
  /** Unique identifier for an API key */
  ApiKeyID: { input: string; output: string; }
  /** Unique identifier for an arrow */
  ArrowID: { input: string; output: string; }
  /** Date with time (isoformat) */
  DateTime: { input: any; output: any; }
  /** Unique identifier for a diagram */
  DiagramID: { input: string; output: string; }
  /** Unique identifier for an execution */
  ExecutionID: { input: string; output: string; }
  /** Unique identifier for a handle (format: nodeId:handleName) */
  HandleID: { input: string; output: string; }
  /** Arbitrary JSON-serializable data */
  JSONScalar: { input: any; output: any; }
  /** Unique identifier for a node */
  NodeID: { input: string; output: string; }
  /** Unique identifier for a person (LLM agent) */
  PersonID: { input: string; output: string; }
};

export type ApiKey = {
  __typename?: 'ApiKey';
  id: Scalars['String']['output'];
  label: Scalars['String']['output'];
  maskedKey: Scalars['String']['output'];
  service: Scalars['String']['output'];
};

export type ApiKeyResult = {
  __typename?: 'ApiKeyResult';
  apiKey?: Maybe<ApiKey>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type Arrow = {
  __typename?: 'Arrow';
  data?: Maybe<Scalars['JSONScalar']['output']>;
  id: Scalars['String']['output'];
  source: Scalars['String']['output'];
  target: Scalars['String']['output'];
};

export type CreateApiKeyInput = {
  key: Scalars['String']['input'];
  label: Scalars['String']['input'];
  service: LlmService;
};

export type CreateArrowInput = {
  label?: InputMaybe<Scalars['String']['input']>;
  source: Scalars['HandleID']['input'];
  target: Scalars['HandleID']['input'];
};

export type CreateDiagramInput = {
  author?: InputMaybe<Scalars['String']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  tags?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type CreateNodeInput = {
  label: Scalars['String']['input'];
  position: Vec2Input;
  properties: Scalars['JSONScalar']['input'];
  type: NodeType;
};

export type CreatePersonInput = {
  apiKeyId: Scalars['ApiKeyID']['input'];
  forgettingMode?: ForgettingMode;
  label: Scalars['String']['input'];
  maxTokens?: InputMaybe<Scalars['Int']['input']>;
  model: Scalars['String']['input'];
  service: LlmService;
  systemPrompt?: InputMaybe<Scalars['String']['input']>;
  temperature?: InputMaybe<Scalars['Float']['input']>;
  topP?: InputMaybe<Scalars['Float']['input']>;
};

export type DeleteResult = {
  __typename?: 'DeleteResult';
  deletedId?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type Diagram = {
  __typename?: 'Diagram';
  apiKeys: Array<ApiKey>;
  arrowCount: Scalars['Int']['output'];
  arrows: Array<Arrow>;
  estimatedCost?: Maybe<Scalars['Float']['output']>;
  handles: Array<Handle>;
  metadata?: Maybe<DiagramMetadata>;
  nodeCount: Scalars['Int']['output'];
  nodes: Array<Node>;
  personCount: Scalars['Int']['output'];
  persons: Array<Person>;
};

export type DiagramFilterInput = {
  author?: InputMaybe<Scalars['String']['input']>;
  createdAfter?: InputMaybe<Scalars['DateTime']['input']>;
  createdBefore?: InputMaybe<Scalars['DateTime']['input']>;
  modifiedAfter?: InputMaybe<Scalars['DateTime']['input']>;
  nameContains?: InputMaybe<Scalars['String']['input']>;
  tags?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type DiagramMetadata = {
  __typename?: 'DiagramMetadata';
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
  diagram?: Maybe<Diagram>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export enum EventType {
  ExecutionAborted = 'EXECUTION_ABORTED',
  ExecutionCompleted = 'EXECUTION_COMPLETED',
  ExecutionFailed = 'EXECUTION_FAILED',
  ExecutionStarted = 'EXECUTION_STARTED',
  InteractivePrompt = 'INTERACTIVE_PROMPT',
  InteractiveResponse = 'INTERACTIVE_RESPONSE',
  NodeCompleted = 'NODE_COMPLETED',
  NodeFailed = 'NODE_FAILED',
  NodePaused = 'NODE_PAUSED',
  NodeProgress = 'NODE_PROGRESS',
  NodeSkipped = 'NODE_SKIPPED',
  NodeStarted = 'NODE_STARTED'
}

export type ExecuteDiagramInput = {
  debugMode?: Scalars['Boolean']['input'];
  diagramId: Scalars['DiagramID']['input'];
  maxIterations?: InputMaybe<Scalars['Int']['input']>;
  timeout?: InputMaybe<Scalars['Int']['input']>;
  variables?: InputMaybe<Scalars['JSONScalar']['input']>;
};

export type ExecutionControlInput = {
  action: Scalars['String']['input'];
  executionId: Scalars['ExecutionID']['input'];
  nodeId?: InputMaybe<Scalars['NodeID']['input']>;
};

export type ExecutionEvent = {
  __typename?: 'ExecutionEvent';
  data: Scalars['JSONScalar']['output'];
  eventType: Scalars['String']['output'];
  executionId: Scalars['ExecutionID']['output'];
  formattedMessage: Scalars['String']['output'];
  nodeId?: Maybe<Scalars['NodeID']['output']>;
  sequence: Scalars['Int']['output'];
  timestamp: Scalars['DateTime']['output'];
};

export type ExecutionFilterInput = {
  activeOnly?: Scalars['Boolean']['input'];
  diagramId?: InputMaybe<Scalars['DiagramID']['input']>;
  startedAfter?: InputMaybe<Scalars['DateTime']['input']>;
  startedBefore?: InputMaybe<Scalars['DateTime']['input']>;
  status?: InputMaybe<ExecutionStatus>;
};

export type ExecutionResult = {
  __typename?: 'ExecutionResult';
  error?: Maybe<Scalars['String']['output']>;
  execution?: Maybe<ExecutionState>;
  executionId?: Maybe<Scalars['ExecutionID']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type ExecutionState = {
  __typename?: 'ExecutionState';
  completedNodes: Array<Scalars['NodeID']['output']>;
  diagramId?: Maybe<Scalars['DiagramID']['output']>;
  durationSeconds?: Maybe<Scalars['Float']['output']>;
  endedAt?: Maybe<Scalars['DateTime']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  failedNodes: Array<Scalars['NodeID']['output']>;
  id: Scalars['ExecutionID']['output'];
  isActive: Scalars['Boolean']['output'];
  nodeOutputs: Scalars['JSONScalar']['output'];
  pausedNodes: Array<Scalars['NodeID']['output']>;
  runningNodes: Array<Scalars['NodeID']['output']>;
  skippedNodes: Array<Scalars['NodeID']['output']>;
  startedAt: Scalars['DateTime']['output'];
  status: ExecutionStatus;
  tokenUsage?: Maybe<TokenUsage>;
  variables: Scalars['JSONScalar']['output'];
};

export enum ExecutionStatus {
  Aborted = 'ABORTED',
  Completed = 'COMPLETED',
  Failed = 'FAILED',
  Paused = 'PAUSED',
  Running = 'RUNNING',
  Started = 'STARTED'
}

export enum ForgettingMode {
  None = 'NONE',
  OnEveryTurn = 'ON_EVERY_TURN',
  UponRequest = 'UPON_REQUEST'
}

export type Handle = {
  __typename?: 'Handle';
  dataType: Scalars['String']['output'];
  direction: Scalars['String']['output'];
  id: Scalars['String']['output'];
  label: Scalars['String']['output'];
  nodeId: Scalars['String']['output'];
  position?: Maybe<Scalars['String']['output']>;
};

export type InteractivePrompt = {
  __typename?: 'InteractivePrompt';
  executionId: Scalars['ExecutionID']['output'];
  nodeId: Scalars['NodeID']['output'];
  prompt: Scalars['String']['output'];
  timeoutSeconds?: Maybe<Scalars['Int']['output']>;
  timestamp: Scalars['DateTime']['output'];
};

export type InteractiveResponseInput = {
  executionId: Scalars['ExecutionID']['input'];
  nodeId: Scalars['NodeID']['input'];
  response: Scalars['String']['input'];
};

export enum LlmService {
  Anthropic = 'ANTHROPIC',
  Bedrock = 'BEDROCK',
  Deepseek = 'DEEPSEEK',
  Google = 'GOOGLE',
  Groq = 'GROQ',
  Openai = 'OPENAI',
  Vertex = 'VERTEX'
}

export type Mutation = {
  __typename?: 'Mutation';
  clearConversations: DeleteResult;
  controlExecution: ExecutionResult;
  createApiKey: ApiKeyResult;
  createArrow: DiagramResult;
  createDiagram: DiagramResult;
  createNode: NodeResult;
  createPerson: PersonResult;
  deleteApiKey: DeleteResult;
  deleteArrow: DeleteResult;
  deleteDiagram: DeleteResult;
  deleteNode: DeleteResult;
  deletePerson: DeleteResult;
  executeDiagram: ExecutionResult;
  submitInteractiveResponse: ExecutionResult;
  testApiKey: TestApiKeyResult;
  updateNode: NodeResult;
  updatePerson: PersonResult;
};


export type MutationControlExecutionArgs = {
  input: ExecutionControlInput;
};


export type MutationCreateApiKeyArgs = {
  input: CreateApiKeyInput;
};


export type MutationCreateArrowArgs = {
  diagramId: Scalars['DiagramID']['input'];
  input: CreateArrowInput;
};


export type MutationCreateDiagramArgs = {
  input: CreateDiagramInput;
};


export type MutationCreateNodeArgs = {
  diagramId: Scalars['DiagramID']['input'];
  input: CreateNodeInput;
};


export type MutationCreatePersonArgs = {
  diagramId: Scalars['DiagramID']['input'];
  input: CreatePersonInput;
};


export type MutationDeleteApiKeyArgs = {
  id: Scalars['ApiKeyID']['input'];
};


export type MutationDeleteArrowArgs = {
  id: Scalars['ArrowID']['input'];
};


export type MutationDeleteDiagramArgs = {
  id: Scalars['DiagramID']['input'];
};


export type MutationDeleteNodeArgs = {
  id: Scalars['NodeID']['input'];
};


export type MutationDeletePersonArgs = {
  id: Scalars['PersonID']['input'];
};


export type MutationExecuteDiagramArgs = {
  input: ExecuteDiagramInput;
};


export type MutationSubmitInteractiveResponseArgs = {
  input: InteractiveResponseInput;
};


export type MutationTestApiKeyArgs = {
  id: Scalars['ApiKeyID']['input'];
};


export type MutationUpdateNodeArgs = {
  input: UpdateNodeInput;
};


export type MutationUpdatePersonArgs = {
  input: UpdatePersonInput;
};

export type Node = {
  __typename?: 'Node';
  data: Scalars['JSONScalar']['output'];
  displayName: Scalars['String']['output'];
  id: Scalars['String']['output'];
  position: Vec2;
  type: Scalars['String']['output'];
};

export type NodeExecution = {
  __typename?: 'NodeExecution';
  error?: Maybe<Scalars['String']['output']>;
  executionId: Scalars['ExecutionID']['output'];
  nodeId: Scalars['NodeID']['output'];
  nodeType: NodeType;
  output?: Maybe<Scalars['JSONScalar']['output']>;
  progress?: Maybe<Scalars['String']['output']>;
  status: Scalars['String']['output'];
  timestamp: Scalars['DateTime']['output'];
  tokensUsed?: Maybe<Scalars['Int']['output']>;
};

export type NodeResult = {
  __typename?: 'NodeResult';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  node?: Maybe<Node>;
  success: Scalars['Boolean']['output'];
};

export enum NodeType {
  Condition = 'CONDITION',
  Db = 'DB',
  Endpoint = 'ENDPOINT',
  Job = 'JOB',
  Notion = 'NOTION',
  PersonBatchJob = 'PERSON_BATCH_JOB',
  PersonJob = 'PERSON_JOB',
  Start = 'START',
  UserResponse = 'USER_RESPONSE'
}

export type Person = {
  __typename?: 'Person';
  apiKeyId: Scalars['String']['output'];
  forgettingMode: Scalars['String']['output'];
  id: Scalars['String']['output'];
  label: Scalars['String']['output'];
  maskedApiKey?: Maybe<Scalars['String']['output']>;
  model: Scalars['String']['output'];
  service: Scalars['String']['output'];
  systemPrompt?: Maybe<Scalars['String']['output']>;
  type: Scalars['String']['output'];
};

export type PersonResult = {
  __typename?: 'PersonResult';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  person?: Maybe<Person>;
  success: Scalars['Boolean']['output'];
};

export type Query = {
  __typename?: 'Query';
  apiKey?: Maybe<ApiKey>;
  apiKeys: Array<ApiKey>;
  availableModels: Array<Scalars['String']['output']>;
  diagram?: Maybe<Diagram>;
  diagrams: Array<Diagram>;
  execution?: Maybe<ExecutionState>;
  executionEvents: Array<ExecutionEvent>;
  executions: Array<ExecutionState>;
  person?: Maybe<Person>;
  persons: Array<Person>;
  systemInfo: Scalars['JSONScalar']['output'];
};


export type QueryApiKeyArgs = {
  id: Scalars['ApiKeyID']['input'];
};


export type QueryApiKeysArgs = {
  service?: InputMaybe<Scalars['String']['input']>;
};


export type QueryAvailableModelsArgs = {
  apiKeyId: Scalars['ApiKeyID']['input'];
  service: Scalars['String']['input'];
};


export type QueryDiagramArgs = {
  id: Scalars['DiagramID']['input'];
};


export type QueryDiagramsArgs = {
  filter?: InputMaybe<DiagramFilterInput>;
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
};


export type QueryExecutionArgs = {
  id: Scalars['ExecutionID']['input'];
};


export type QueryExecutionEventsArgs = {
  executionId: Scalars['ExecutionID']['input'];
  limit?: Scalars['Int']['input'];
  sinceSequence?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryExecutionsArgs = {
  filter?: InputMaybe<ExecutionFilterInput>;
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
};


export type QueryPersonArgs = {
  id: Scalars['PersonID']['input'];
};


export type QueryPersonsArgs = {
  limit?: Scalars['Int']['input'];
};

export type Subscription = {
  __typename?: 'Subscription';
  diagramChanges: Diagram;
  executionEvents: ExecutionEvent;
  executionUpdates: ExecutionState;
  interactivePrompts: InteractivePrompt;
  nodeUpdates: NodeExecution;
};


export type SubscriptionDiagramChangesArgs = {
  diagramId: Scalars['DiagramID']['input'];
};


export type SubscriptionExecutionEventsArgs = {
  eventTypes?: InputMaybe<Array<EventType>>;
  executionId: Scalars['ExecutionID']['input'];
};


export type SubscriptionExecutionUpdatesArgs = {
  executionId: Scalars['ExecutionID']['input'];
};


export type SubscriptionInteractivePromptsArgs = {
  executionId: Scalars['ExecutionID']['input'];
};


export type SubscriptionNodeUpdatesArgs = {
  executionId: Scalars['ExecutionID']['input'];
  nodeTypes?: InputMaybe<Array<NodeType>>;
};

export type TestApiKeyResult = {
  __typename?: 'TestApiKeyResult';
  availableModels?: Maybe<Array<Scalars['String']['output']>>;
  error?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
  valid: Scalars['Boolean']['output'];
};

export type TokenUsage = {
  __typename?: 'TokenUsage';
  cached?: Maybe<Scalars['Int']['output']>;
  input: Scalars['Int']['output'];
  output: Scalars['Int']['output'];
  total: Scalars['Int']['output'];
};

export type UpdateNodeInput = {
  id: Scalars['NodeID']['input'];
  label?: InputMaybe<Scalars['String']['input']>;
  position?: InputMaybe<Vec2Input>;
  properties?: InputMaybe<Scalars['JSONScalar']['input']>;
};

export type UpdatePersonInput = {
  apiKeyId?: InputMaybe<Scalars['ApiKeyID']['input']>;
  forgettingMode?: InputMaybe<ForgettingMode>;
  id: Scalars['PersonID']['input'];
  label?: InputMaybe<Scalars['String']['input']>;
  maxTokens?: InputMaybe<Scalars['Int']['input']>;
  model?: InputMaybe<Scalars['String']['input']>;
  systemPrompt?: InputMaybe<Scalars['String']['input']>;
  temperature?: InputMaybe<Scalars['Float']['input']>;
};

export type Vec2 = {
  __typename?: 'Vec2';
  x: Scalars['Float']['output'];
  y: Scalars['Float']['output'];
};

export type Vec2Input = {
  x: Scalars['Float']['input'];
  y: Scalars['Float']['input'];
};

export type GetApiKeysQueryVariables = Exact<{
  service?: InputMaybe<Scalars['String']['input']>;
}>;


export type GetApiKeysQuery = { __typename?: 'Query', apiKeys: Array<{ __typename?: 'ApiKey', id: string, label: string, service: string, maskedKey: string }> };

export type GetApiKeyQueryVariables = Exact<{
  id: Scalars['ApiKeyID']['input'];
}>;


export type GetApiKeyQuery = { __typename?: 'Query', apiKey?: { __typename?: 'ApiKey', id: string, label: string, service: string, maskedKey: string } | null };

export type GetAvailableModelsQueryVariables = Exact<{
  service: Scalars['String']['input'];
  apiKeyId: Scalars['ApiKeyID']['input'];
}>;


export type GetAvailableModelsQuery = { __typename?: 'Query', availableModels: Array<string> };

export type CreateApiKeyMutationVariables = Exact<{
  input: CreateApiKeyInput;
}>;


export type CreateApiKeyMutation = { __typename?: 'Mutation', createApiKey: { __typename?: 'ApiKeyResult', success: boolean, message?: string | null, error?: string | null, apiKey?: { __typename?: 'ApiKey', id: string, label: string, service: string, maskedKey: string } | null } };

export type TestApiKeyMutationVariables = Exact<{
  id: Scalars['ApiKeyID']['input'];
}>;


export type TestApiKeyMutation = { __typename?: 'Mutation', testApiKey: { __typename?: 'TestApiKeyResult', success: boolean, valid: boolean, availableModels?: Array<string> | null, error?: string | null } };

export type DeleteApiKeyMutationVariables = Exact<{
  id: Scalars['ApiKeyID']['input'];
}>;


export type DeleteApiKeyMutation = { __typename?: 'Mutation', deleteApiKey: { __typename?: 'DeleteResult', success: boolean, deletedId?: string | null, message?: string | null, error?: string | null } };

export type ClearConversationsMutationVariables = Exact<{ [key: string]: never; }>;


export type ClearConversationsMutation = { __typename?: 'Mutation', clearConversations: { __typename?: 'DeleteResult', success: boolean, message?: string | null, error?: string | null } };

export type GetDiagramQueryVariables = Exact<{
  id: Scalars['DiagramID']['input'];
}>;


export type GetDiagramQuery = { __typename?: 'Query', diagram?: { __typename?: 'Diagram', nodes: Array<{ __typename?: 'Node', id: string, type: string, displayName: string, data: any, position: { __typename?: 'Vec2', x: number, y: number } }>, handles: Array<{ __typename?: 'Handle', id: string, nodeId: string, label: string, direction: string, dataType: string, position?: string | null }>, arrows: Array<{ __typename?: 'Arrow', id: string, source: string, target: string, data?: any | null }>, persons: Array<{ __typename?: 'Person', id: string, label: string, service: string, model: string, systemPrompt?: string | null, apiKeyId: string, forgettingMode: string, maskedApiKey?: string | null }>, apiKeys: Array<{ __typename?: 'ApiKey', id: string, label: string, service: string, maskedKey: string }>, metadata?: { __typename?: 'DiagramMetadata', id?: string | null, name?: string | null, description?: string | null, version: string, created: string, modified: string, author?: string | null, tags?: Array<string> | null } | null } | null };

export type ListDiagramsQueryVariables = Exact<{
  filter?: InputMaybe<DiagramFilterInput>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ListDiagramsQuery = { __typename?: 'Query', diagrams: Array<{ __typename?: 'Diagram', nodeCount: number, arrowCount: number, personCount: number, metadata?: { __typename?: 'DiagramMetadata', id?: string | null, name?: string | null, description?: string | null, author?: string | null, created: string, modified: string, tags?: Array<string> | null } | null }> };

export type CreateDiagramMutationVariables = Exact<{
  input: CreateDiagramInput;
}>;


export type CreateDiagramMutation = { __typename?: 'Mutation', createDiagram: { __typename?: 'DiagramResult', success: boolean, message?: string | null, error?: string | null, diagram?: { __typename?: 'Diagram', metadata?: { __typename?: 'DiagramMetadata', id?: string | null, name?: string | null } | null } | null } };

export type ExecuteDiagramMutationVariables = Exact<{
  input: ExecuteDiagramInput;
}>;


export type ExecuteDiagramMutation = { __typename?: 'Mutation', executeDiagram: { __typename?: 'ExecutionResult', success: boolean, executionId?: string | null, message?: string | null, error?: string | null } };

export type DeleteDiagramMutationVariables = Exact<{
  id: Scalars['DiagramID']['input'];
}>;


export type DeleteDiagramMutation = { __typename?: 'Mutation', deleteDiagram: { __typename?: 'DeleteResult', success: boolean, deletedId?: string | null, message?: string | null, error?: string | null } };

export type GetExecutionQueryVariables = Exact<{
  id: Scalars['ExecutionID']['input'];
}>;


export type GetExecutionQuery = { __typename?: 'Query', execution?: { __typename?: 'ExecutionState', id: string, status: ExecutionStatus, diagramId?: string | null, startedAt: any, endedAt?: any | null, runningNodes: Array<string>, completedNodes: Array<string>, skippedNodes: Array<string>, pausedNodes: Array<string>, failedNodes: Array<string>, nodeOutputs: any, variables: any, error?: string | null, durationSeconds?: number | null, isActive: boolean, tokenUsage?: { __typename?: 'TokenUsage', input: number, output: number, cached?: number | null, total: number } | null } | null };

export type ListExecutionsQueryVariables = Exact<{
  filter?: InputMaybe<ExecutionFilterInput>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}>;


export type ListExecutionsQuery = { __typename?: 'Query', executions: Array<{ __typename?: 'ExecutionState', id: string, status: ExecutionStatus, diagramId?: string | null, startedAt: any, endedAt?: any | null, isActive: boolean, durationSeconds?: number | null }> };

export type ExecutionUpdatesSubscriptionVariables = Exact<{
  executionId: Scalars['ExecutionID']['input'];
}>;


export type ExecutionUpdatesSubscription = { __typename?: 'Subscription', executionUpdates: { __typename?: 'ExecutionState', id: string, status: ExecutionStatus, runningNodes: Array<string>, completedNodes: Array<string>, failedNodes: Array<string>, nodeOutputs: any, error?: string | null, tokenUsage?: { __typename?: 'TokenUsage', total: number } | null } };

export type NodeUpdatesSubscriptionVariables = Exact<{
  executionId: Scalars['ExecutionID']['input'];
  nodeTypes?: InputMaybe<Array<NodeType> | NodeType>;
}>;


export type NodeUpdatesSubscription = { __typename?: 'Subscription', nodeUpdates: { __typename?: 'NodeExecution', executionId: string, nodeId: string, nodeType: NodeType, status: string, progress?: string | null, output?: any | null, error?: string | null, tokensUsed?: number | null, timestamp: any } };

export type InteractivePromptsSubscriptionVariables = Exact<{
  executionId: Scalars['ExecutionID']['input'];
}>;


export type InteractivePromptsSubscription = { __typename?: 'Subscription', interactivePrompts: { __typename?: 'InteractivePrompt', executionId: string, nodeId: string, prompt: string, timeoutSeconds?: number | null, timestamp: any } };

export type ControlExecutionMutationVariables = Exact<{
  input: ExecutionControlInput;
}>;


export type ControlExecutionMutation = { __typename?: 'Mutation', controlExecution: { __typename?: 'ExecutionResult', success: boolean, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionState', id: string, status: ExecutionStatus } | null } };

export type SubmitInteractiveResponseMutationVariables = Exact<{
  input: InteractiveResponseInput;
}>;


export type SubmitInteractiveResponseMutation = { __typename?: 'Mutation', submitInteractiveResponse: { __typename?: 'ExecutionResult', success: boolean, message?: string | null, error?: string | null, execution?: { __typename?: 'ExecutionState', id: string, status: ExecutionStatus, runningNodes: Array<string> } | null } };

export type CreateNodeMutationVariables = Exact<{
  diagramId: Scalars['DiagramID']['input'];
  input: CreateNodeInput;
}>;


export type CreateNodeMutation = { __typename?: 'Mutation', createNode: { __typename?: 'NodeResult', success: boolean, message?: string | null, error?: string | null, node?: { __typename?: 'Node', id: string, type: string, displayName: string, data: any, position: { __typename?: 'Vec2', x: number, y: number } } | null } };

export type UpdateNodeMutationVariables = Exact<{
  input: UpdateNodeInput;
}>;


export type UpdateNodeMutation = { __typename?: 'Mutation', updateNode: { __typename?: 'NodeResult', success: boolean, message?: string | null, error?: string | null, node?: { __typename?: 'Node', id: string, type: string, displayName: string, data: any, position: { __typename?: 'Vec2', x: number, y: number } } | null } };

export type DeleteNodeMutationVariables = Exact<{
  id: Scalars['NodeID']['input'];
}>;


export type DeleteNodeMutation = { __typename?: 'Mutation', deleteNode: { __typename?: 'DeleteResult', success: boolean, deletedId?: string | null, message?: string | null, error?: string | null } };

export type CreateArrowMutationVariables = Exact<{
  diagramId: Scalars['DiagramID']['input'];
  input: CreateArrowInput;
}>;


export type CreateArrowMutation = { __typename?: 'Mutation', createArrow: { __typename?: 'DiagramResult', success: boolean, message?: string | null, error?: string | null, diagram?: { __typename?: 'Diagram', arrows: Array<{ __typename?: 'Arrow', id: string, source: string, target: string, data?: any | null }> } | null } };

export type DeleteArrowMutationVariables = Exact<{
  id: Scalars['ArrowID']['input'];
}>;


export type DeleteArrowMutation = { __typename?: 'Mutation', deleteArrow: { __typename?: 'DeleteResult', success: boolean, deletedId?: string | null, message?: string | null, error?: string | null } };

export type GetPersonQueryVariables = Exact<{
  id: Scalars['PersonID']['input'];
}>;


export type GetPersonQuery = { __typename?: 'Query', person?: { __typename?: 'Person', id: string, label: string, service: string, model: string, apiKeyId: string, systemPrompt?: string | null, forgettingMode: string, maskedApiKey?: string | null, type: string } | null };

export type GetPersonsQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Int']['input']>;
}>;


export type GetPersonsQuery = { __typename?: 'Query', persons: Array<{ __typename?: 'Person', id: string, label: string, service: string, model: string, apiKeyId: string, systemPrompt?: string | null, forgettingMode: string, maskedApiKey?: string | null, type: string }> };

export type CreatePersonMutationVariables = Exact<{
  diagramId: Scalars['DiagramID']['input'];
  input: CreatePersonInput;
}>;


export type CreatePersonMutation = { __typename?: 'Mutation', createPerson: { __typename?: 'PersonResult', success: boolean, message?: string | null, error?: string | null, person?: { __typename?: 'Person', id: string, label: string, service: string, model: string, apiKeyId: string, systemPrompt?: string | null, forgettingMode: string, maskedApiKey?: string | null, type: string } | null } };

export type UpdatePersonMutationVariables = Exact<{
  input: UpdatePersonInput;
}>;


export type UpdatePersonMutation = { __typename?: 'Mutation', updatePerson: { __typename?: 'PersonResult', success: boolean, message?: string | null, error?: string | null, person?: { __typename?: 'Person', id: string, label: string, service: string, model: string, apiKeyId: string, systemPrompt?: string | null, forgettingMode: string, maskedApiKey?: string | null, type: string } | null } };

export type DeletePersonMutationVariables = Exact<{
  id: Scalars['PersonID']['input'];
}>;


export type DeletePersonMutation = { __typename?: 'Mutation', deletePerson: { __typename?: 'DeleteResult', success: boolean, deletedId?: string | null, message?: string | null, error?: string | null } };

export type GetSystemInfoQueryVariables = Exact<{ [key: string]: never; }>;


export type GetSystemInfoQuery = { __typename?: 'Query', systemInfo: any };


export const GetApiKeysDocument = gql`
    query GetApiKeys($service: String) {
  apiKeys(service: $service) {
    id
    label
    service
    maskedKey
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
  apiKey(id: $id) {
    id
    label
    service
    maskedKey
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
  availableModels(service: $service, apiKeyId: $apiKeyId)
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
  createApiKey(input: $input) {
    success
    apiKey {
      id
      label
      service
      maskedKey
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
  testApiKey(id: $id) {
    success
    valid
    availableModels
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
  deleteApiKey(id: $id) {
    success
    deletedId
    message
    error
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
export const ClearConversationsDocument = gql`
    mutation ClearConversations {
  clearConversations {
    success
    message
    error
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
      displayName
      data
    }
    handles {
      id
      nodeId
      label
      direction
      dataType
      position
    }
    arrows {
      id
      source
      target
      data
    }
    persons {
      id
      label
      service
      model
      systemPrompt
      apiKeyId
      forgettingMode
      maskedApiKey
    }
    apiKeys {
      id
      label
      service
      maskedKey
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
    personCount
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
  createDiagram(input: $input) {
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
  executeDiagram(input: $input) {
    success
    executionId
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
    mutation DeleteDiagram($id: DiagramID!) {
  deleteDiagram(id: $id) {
    success
    deletedId
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
    diagramId
    startedAt
    endedAt
    runningNodes
    completedNodes
    skippedNodes
    pausedNodes
    failedNodes
    nodeOutputs
    variables
    tokenUsage {
      input
      output
      cached
      total
    }
    error
    durationSeconds
    isActive
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
    diagramId
    startedAt
    endedAt
    isActive
    durationSeconds
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
  executionUpdates(executionId: $executionId) {
    id
    status
    runningNodes
    completedNodes
    failedNodes
    nodeOutputs
    tokenUsage {
      total
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
  nodeUpdates(executionId: $executionId, nodeTypes: $nodeTypes) {
    executionId
    nodeId
    nodeType
    status
    progress
    output
    error
    tokensUsed
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
  interactivePrompts(executionId: $executionId) {
    executionId
    nodeId
    prompt
    timeoutSeconds
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
    mutation ControlExecution($input: ExecutionControlInput!) {
  controlExecution(input: $input) {
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
export const SubmitInteractiveResponseDocument = gql`
    mutation SubmitInteractiveResponse($input: InteractiveResponseInput!) {
  submitInteractiveResponse(input: $input) {
    success
    execution {
      id
      status
      runningNodes
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
 *      input: // value for 'input'
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
export const CreateNodeDocument = gql`
    mutation CreateNode($diagramId: DiagramID!, $input: CreateNodeInput!) {
  createNode(diagramId: $diagramId, input: $input) {
    success
    node {
      id
      type
      displayName
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
    mutation UpdateNode($input: UpdateNodeInput!) {
  updateNode(input: $input) {
    success
    node {
      id
      type
      displayName
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
    mutation DeleteNode($id: NodeID!) {
  deleteNode(id: $id) {
    success
    deletedId
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
 *      id: // value for 'id'
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
export const CreateArrowDocument = gql`
    mutation CreateArrow($diagramId: DiagramID!, $input: CreateArrowInput!) {
  createArrow(diagramId: $diagramId, input: $input) {
    success
    diagram {
      arrows {
        id
        source
        target
        data
      }
    }
    message
    error
  }
}
    `;
export type CreateArrowMutationFn = Apollo.MutationFunction<CreateArrowMutation, CreateArrowMutationVariables>;

/**
 * __useCreateArrowMutation__
 *
 * To run a mutation, you first call `useCreateArrowMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useCreateArrowMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [createArrowMutation, { data, loading, error }] = useCreateArrowMutation({
 *   variables: {
 *      diagramId: // value for 'diagramId'
 *      input: // value for 'input'
 *   },
 * });
 */
export function useCreateArrowMutation(baseOptions?: Apollo.MutationHookOptions<CreateArrowMutation, CreateArrowMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<CreateArrowMutation, CreateArrowMutationVariables>(CreateArrowDocument, options);
      }
export type CreateArrowMutationHookResult = ReturnType<typeof useCreateArrowMutation>;
export type CreateArrowMutationResult = Apollo.MutationResult<CreateArrowMutation>;
export type CreateArrowMutationOptions = Apollo.BaseMutationOptions<CreateArrowMutation, CreateArrowMutationVariables>;
export const DeleteArrowDocument = gql`
    mutation DeleteArrow($id: ArrowID!) {
  deleteArrow(id: $id) {
    success
    deletedId
    message
    error
  }
}
    `;
export type DeleteArrowMutationFn = Apollo.MutationFunction<DeleteArrowMutation, DeleteArrowMutationVariables>;

/**
 * __useDeleteArrowMutation__
 *
 * To run a mutation, you first call `useDeleteArrowMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useDeleteArrowMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [deleteArrowMutation, { data, loading, error }] = useDeleteArrowMutation({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useDeleteArrowMutation(baseOptions?: Apollo.MutationHookOptions<DeleteArrowMutation, DeleteArrowMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<DeleteArrowMutation, DeleteArrowMutationVariables>(DeleteArrowDocument, options);
      }
export type DeleteArrowMutationHookResult = ReturnType<typeof useDeleteArrowMutation>;
export type DeleteArrowMutationResult = Apollo.MutationResult<DeleteArrowMutation>;
export type DeleteArrowMutationOptions = Apollo.BaseMutationOptions<DeleteArrowMutation, DeleteArrowMutationVariables>;
export const GetPersonDocument = gql`
    query GetPerson($id: PersonID!) {
  person(id: $id) {
    id
    label
    service
    model
    apiKeyId
    systemPrompt
    forgettingMode
    maskedApiKey
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
    service
    model
    apiKeyId
    systemPrompt
    forgettingMode
    maskedApiKey
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
    mutation CreatePerson($diagramId: DiagramID!, $input: CreatePersonInput!) {
  createPerson(diagramId: $diagramId, input: $input) {
    success
    person {
      id
      label
      service
      model
      apiKeyId
      systemPrompt
      forgettingMode
      maskedApiKey
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
    mutation UpdatePerson($input: UpdatePersonInput!) {
  updatePerson(input: $input) {
    success
    person {
      id
      label
      service
      model
      apiKeyId
      systemPrompt
      forgettingMode
      maskedApiKey
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
    mutation DeletePerson($id: PersonID!) {
  deletePerson(id: $id) {
    success
    deletedId
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
export const GetSystemInfoDocument = gql`
    query GetSystemInfo {
  systemInfo
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