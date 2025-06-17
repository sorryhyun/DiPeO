import type { Dict } from '@/core/types';
import {NodeID, ExecutionID, PersonID} from '@/core/types';

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