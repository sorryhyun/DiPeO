import {
  type ExecutionOptions as CanonicalExecutionOptions,
  ExecutionStatus,
  EventType,
  NodeExecutionStatus,
} from '@dipeo/models';

// Re-export canonical types that don't need adaptation
export type { 
  PersonMemoryMessage,
  TokenUsage,
} from '@dipeo/models';

// Export the already imported enums
export { ExecutionStatus, NodeExecutionStatus, EventType };

// Re-export from message for convenience
export type { InteractivePromptData } from './message';


// Use canonical ExecutionOptions directly  
export type ExecutionOptions = CanonicalExecutionOptions;