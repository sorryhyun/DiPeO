import type { Dict } from '../primitives';
import type { NodeID, ExecutionID, PersonID } from '../branded';

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