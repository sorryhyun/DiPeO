import { PersonID, MemoryConfig } from "./diagram.js";

/**
 * Base message interface for conversations
 * Used by both execution (PersonMemory) and person domains
 */
export interface Message {
  id?: string;
  fromPersonId: PersonID | 'system';  // Who sent the message
  toPersonId: PersonID;               // Who receives/stores this message
  content: string;
  timestamp?: string;
  tokenCount?: number;
  messageType: 'person_to_person' | 'system_to_person' | 'person_to_system';
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
  messages: Message[];
  metadata?: ConversationMetadata;
}


export interface MemoryState extends Conversation {
  visibleMessages: number;
  hasMore?: boolean;
  config?: MemoryConfig;
}