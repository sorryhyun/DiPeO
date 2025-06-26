import type { Dict } from '@/core/types';
import type { NodeID, ExecutionID, PersonID } from '@dipeo/domain-models';

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

export interface ConversationMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  personId: PersonID;
  content: string;
  timestamp?: string;
  tokenCount?: number;
  nodeLabel?: string;
}

export interface PersonMemoryState {
  messages: ConversationMessage[];
  visibleMessages: number;
  hasMore: boolean;
  config: {
    forgetMode: 'no_forget' | 'forget_after_messages' | 'forget_after_time';
    maxMessages?: number;
  };
}