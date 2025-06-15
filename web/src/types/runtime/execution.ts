import type { Dict } from '../primitives';
import type { NodeID, ExecutionID, PersonID } from '../branded';
// PersonMemoryConfig is defined below

export interface ExecutionOptions {
  mode?: 'monitor' | 'headless' | 'check';
  debug?: boolean;
  delay?: number;
  continueOnError?: boolean;
  allowPartial?: boolean;
  debugMode?: boolean;
}

export interface ExecutionState<C = Dict> {
  id: ExecutionID;
  running: NodeID[];
  completed: NodeID[];
  skipped: NodeID[];
  paused: NodeID[];
  context: C;
  errors: Dict<string>;
  isRunning: boolean;
  startedAt?: string;
  endedAt?: string;
  totalTokens?: number;
}

export interface ExecutionUpdate {
  type: string;
  executionId?: ExecutionID;
  node_id?: string;
  progress?: string;
  output?: unknown;
  output_preview?: string;
  error?: string;
  status?: string;
  total_nodes?: number;
  context?: Dict;
  duration?: number;
  nodeType?: string;
  nodeId?: NodeID;
  message?: string;
  details?: Dict;
  totalTokens?: number;
  tokens?: number;
  timestamp?: string;
  conversationId?: string;
}

export interface ExecutionResult {
  success?: boolean;
  executionId?: ExecutionID;
  context?: Record<string, unknown>;
  totalTokens?: number;
  duration?: number;
  finalContext?: Record<string, unknown>;
  error?: string;
  metadata?: {
    totalTokens?: number;
    executionTime?: number;
  };
}

// Re-export from message for convenience
export type { InteractivePromptData } from './message';

// Memory types
export interface ExecutionPersonMemoryConfig {
  forgetMode?: 'no_forget' | 'on_every_turn' | 'upon_request';
  maxMessages?: number;
  temperature?: number;
}

export interface PersonMemoryState {
  personId: PersonID;
  messages: Array<{
    id?: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: string;
    tokenCount?: number;
  }>;
  visibleMessages: number;
  hasMore?: boolean;
  config?: PersonMemoryConfig;
}

// PersonMemoryConfig definition
export interface PersonMemoryConfig {
  forgetMode?: 'no_forget' | 'on_every_turn' | 'upon_request';
  maxMessages?: number;
  temperature?: number;
}