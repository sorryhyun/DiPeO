import {
  type ExecutionOptions as CanonicalExecutionOptions,
  Status,
  EventType,
} from '@dipeo/models';

// Re-export canonical types that don't need adaptation
export type { 
  PersonMemoryMessage,
  LLMUsage,
} from '@dipeo/models';

// Export the already imported enums and types
export { Status, EventType };

// Re-export from message for convenience
export type { InteractivePromptData } from './message';


// Use canonical ExecutionOptions directly  
export type ExecutionOptions = CanonicalExecutionOptions;