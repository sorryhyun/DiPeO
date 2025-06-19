import { PersonID } from "./index.js";

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

/**
 * Conversation metadata for tracking statistics
 */
export interface ConversationMetadata {
  startedAt: string;
  lastMessageAt: string;
  totalTokens: number;
  messageCount: number;
  contextResets: number;
}

/**
 * Base conversation interface
 */
export interface Conversation {
  personId: PersonID;
  messages: Message[];
  metadata?: ConversationMetadata;
}

/**
 * Memory configuration for execution context
 */
export interface MemoryConfig {
  forgetMode?: 'no_forget' | 'on_every_turn' | 'upon_request';
  maxMessages?: number;
  temperature?: number;
}

/**
 * Memory state for execution context
 * Extends Conversation with pagination and config
 */
export interface MemoryState extends Conversation {
  visibleMessages: number;
  hasMore?: boolean;
  config?: MemoryConfig;
}