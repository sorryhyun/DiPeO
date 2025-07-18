import { PersonID, MemoryConfig } from "./diagram.js";

// Branded types for IDs
export type MessageID = string & { readonly __brand: 'MessageID' };

/**
 * Base message interface for conversations
 * Used by both execution (PersonMemory) and person domains
 */
export interface Message {
  id?: string;
  from_person_id: PersonID | 'system';  // Who sent the message
  to_person_id: PersonID;               // Who receives/stores this message
  content: string;
  timestamp?: string;
  token_count?: number;
  message_type: 'person_to_person' | 'system_to_person' | 'person_to_system';
  metadata?: Record<string, any>;
}

export interface ConversationMetadata {
  started_at: string;
  last_message_at: string;
  total_tokens: number;
  message_count: number;
  context_resets: number;
}

export interface Conversation {
  messages: Message[];
  metadata?: ConversationMetadata;
}


export interface MemoryState extends Conversation {
  visible_messages: number;
  has_more?: boolean;
  config?: MemoryConfig;
}