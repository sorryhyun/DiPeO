import { PersonID } from "./diagram.js";

/**
 * Base message interface for conversations
 * Used by both execution (PersonMemory) and person domains
 */
export interface Message {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  tokenCount?: number;
  metadata?: Record<string, any>;
}

export interface ConversationMetadata {
  startedAt: string;
  lastMessageAt: string;
  totalTokens: number;
  messageCount: number;
  contextResets: number;
}

export interface Conversation {
  personId: PersonID;
  messages: Message[];
  metadata?: ConversationMetadata;
}

export interface MemoryConfig {
  forgetMode?: 'no_forget' | 'on_every_turn' | 'upon_request';
  maxMessages?: number;
  temperature?: number;
}

export interface MemoryState extends Conversation {
  visibleMessages: number;
  hasMore?: boolean;
  config?: MemoryConfig;
}