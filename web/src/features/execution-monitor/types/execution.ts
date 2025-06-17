import type { Dict } from '@/core/types';
import type { NodeID, ExecutionID, PersonID } from '@/core/types';

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

// Re-export from message for convenience
export type { InteractivePromptData } from './message';

// Memory types
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

export interface PersonMemoryConfig {
  forgetMode?: 'no_forget' | 'on_every_turn' | 'upon_request';
  maxMessages?: number;
  temperature?: number;
}

// Execution options for running diagrams
export interface ExecutionOptions {
  mode?: 'normal' | 'debug' | 'monitor';
  timeout?: number;
  variables?: Record<string, any>;
  debug?: boolean;
}

// Execution update event
export interface ExecutionUpdate {
  type: 'node_update' | 'execution_start' | 'execution_end' | 'error' | 
        'execution_complete' | 'execution_error' | 'execution_aborted' |
        'node_start' | 'node_complete' | 'node_error' | 'node_skipped' |
        'node_paused' | 'node_progress' | 'interactive_prompt_request' |
        'execution_started';
  nodeId?: string;
  status?: 'running' | 'completed' | 'failed' | 'skipped' | 'paused';
  result?: any;
  error?: string;
  timestamp?: string;
  totalTokens?: number;
  nodeType?: string;
  tokens?: number;
}