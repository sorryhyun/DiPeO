export interface ConversationMessage {
  id: string;
  role: 'assistant' | 'user';
  content: string;
  timestamp: string;
  senderPersonId: string;
  executionId: string;
  nodeId?: string;
  nodeLabel?: string;
  tokenCount?: number;
  cost?: number;
}

export interface PersonMemoryState {
  personId: string;
  messages: ConversationMessage[];
  totalMessages: number;
  visibleMessages: number;
  forgottenMessages: number;
  hasMore: boolean;
}

export interface ConversationFilters {
  searchTerm: string;
  executionId: string;
  showForgotten: boolean;
  startTime?: string;
  endTime?: string;
}