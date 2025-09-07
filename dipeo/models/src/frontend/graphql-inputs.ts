/**
 * GraphQL Input Types
 *
 * This file defines all GraphQL input types used in mutations and queries.
 * These types are shared between the generated GraphQL types and query definitions.
 */

import type { NodeType } from '../core/enums/node-types';
import type { LLMService } from '../core/enums/integrations';
import { APIServiceType } from '../core/enums/integrations';
import type { DiagramFormat } from '../core/enums/diagram';
import type { Status } from '../core/enums/execution';
import type { ExecutionID } from '../core/execution';
import type {
  NodeID,
  PersonID,
  DiagramID,
  ApiKeyID,
  ArrowID,
  HandleID
} from '../core/diagram';

// Re-export enums for convenience
export { DiagramFormat, APIServiceType };

// Helper types
export type InputMaybe<T> = T | null | undefined;

// Scalars type definition for GraphQL scalars
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
  /** The `JSON` scalar type represents JSON values */
  JSON: { input: any; output: any; }
  /** Unique identifier for nodes */
  NodeID: { input: NodeID; output: NodeID; }
  /** Unique identifier for persons */
  PersonID: { input: PersonID; output: PersonID; }
  /** Unique identifier for tasks */
  TaskID: { input: any; output: any; }
  Upload: { input: any; output: any; }
};

// Basic input types
export type Vec2Input = {
  x: Scalars['Float']['input'];
  y: Scalars['Float']['input'];
};

export type PersonLLMConfigInput = {
  api_key_id: Scalars['ID']['input'];
  model: Scalars['String']['input'];
  service: LLMService;
  system_prompt?: InputMaybe<Scalars['String']['input']>;
};

// Node-related inputs
export type CreateNodeInput = {
  data: Scalars['JSON']['input'];
  position: Vec2Input;
  type: NodeType;
};

export type UpdateNodeInput = {
  data?: InputMaybe<Scalars['JSON']['input']>;
  position?: InputMaybe<Vec2Input>;
};

// Diagram-related inputs
export type CreateDiagramInput = {
  author?: InputMaybe<Scalars['String']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  tags?: Array<Scalars['String']['input']>;
};

export type DiagramFilterInput = {
  author?: InputMaybe<Scalars['String']['input']>;
  created_after?: InputMaybe<Scalars['DateTime']['input']>;
  created_before?: InputMaybe<Scalars['DateTime']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  tags?: InputMaybe<Array<Scalars['String']['input']>>;
};

// Person-related inputs
export type CreatePersonInput = {
  label: Scalars['String']['input'];
  llm_config: PersonLLMConfigInput;
  type?: Scalars['String']['input'];
};

export type UpdatePersonInput = {
  label?: InputMaybe<Scalars['String']['input']>;
  llm_config?: InputMaybe<PersonLLMConfigInput>;
};

// API Key inputs
export type CreateApiKeyInput = {
  key: Scalars['String']['input'];
  label: Scalars['String']['input'];
  service: APIServiceType;
};

// Execution-related inputs
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

export type UpdateNodeStateInput = {
  error?: InputMaybe<Scalars['String']['input']>;
  execution_id: Scalars['ID']['input'];
  node_id: Scalars['ID']['input'];
  output?: InputMaybe<Scalars['JSON']['input']>;
  status: Status;
};

// Interactive response input
export type InteractiveResponseInput = {
  execution_id: Scalars['ID']['input'];
  metadata?: InputMaybe<Scalars['JSON']['input']>;
  node_id: Scalars['ID']['input'];
  response: Scalars['String']['input'];
};

// CLI Session inputs
export type RegisterCliSessionInput = {
  execution_id: Scalars['ID']['input'];
  diagram_name: Scalars['String']['input'];
  diagram_format: DiagramFormat;
  diagram_data?: InputMaybe<Scalars['JSON']['input']>;
};

export type UnregisterCliSessionInput = {
  execution_id: Scalars['ID']['input'];
};
