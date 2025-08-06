import type { Dict } from './utilities';
import type { NodeID, ExecutionID, PersonID } from './domain';

export interface InteractivePromptData {
  nodeId: NodeID;
  prompt: string;
  timeout?: number;
  executionId?: ExecutionID;
  context?: Dict;
}

export interface ConversationFilters {
  searchTerm?: string;
  executionId?: ExecutionID;
  showForgotten?: boolean;
  startTime?: string;
  endTime?: string;
}

// UI-specific conversation message with additional display fields
export interface UIConversationMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  personId: PersonID;
  content: string;
  timestamp?: string;
  tokenCount?: number;
  nodeLabel?: string;
}

// UI-specific memory state for display purposes
export interface UIPersonMemoryState {
  messages: UIConversationMessage[];
  visibleMessages: number;
  hasMore: boolean;
  config: {
    forgetMode: 'no_forget' | 'forget_after_messages' | 'forget_after_time';
    maxMessages?: number;
  };
}