import type { Dict } from '../primitives';
import {NodeID, ExecutionID, PersonID} from '../branded';

export type WSMessage = { type: string; [key: string]: unknown };

export type MessageHandler = (message: WSMessage) => void;

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