import {
  type ExecutionOptions as CanonicalExecutionOptions,
  type PersonMemoryState as CanonicalPersonMemoryState,
  ExecutionStatus,
  EventType,
  NodeExecutionStatus,
} from '@dipeo/domain-models';

// Re-export canonical types that don't need adaptation
export type { 
  PersonMemoryConfig,
  PersonMemoryMessage,
  TokenUsage,
} from '@dipeo/domain-models';

// Export the already imported enums
export { ExecutionStatus, NodeExecutionStatus, EventType };

// Re-export from message for convenience
export type { InteractivePromptData } from './message';

// Use canonical PersonMemoryState directly
export type PersonMemoryState = CanonicalPersonMemoryState;

// Use canonical ExecutionOptions directly  
export type ExecutionOptions = CanonicalExecutionOptions;