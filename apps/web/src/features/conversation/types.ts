export interface ConversationMessage {
  id: string;
  role: 'assistant' | 'user';
  content: string;
  timestamp: string;
  sender_person_id: string;
  execution_id: string;
  node_id?: string;
  node_label?: string;
  token_count?: number;
  cost?: number;
}

export interface PersonMemoryState {
  person_id: string;
  messages: ConversationMessage[];
  total_messages: number;
  visible_messages: number;
  forgotten_messages: number;
  has_more: boolean;
}

export interface ConversationFilters {
  searchTerm: string;
  executionId: string;
  showForgotten: boolean;
  startTime?: string;
  endTime?: string;
}