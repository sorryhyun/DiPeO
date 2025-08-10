import { PersonID } from "./diagram.js";
import { JsonDict } from "./types/json.js";

/**
 * Base message interface for conversations
 * Used by both execution (PersonMemory) and person domains
 */
export interface Message {
  id?: string;
  from_person_id: PersonID | 'system';
  to_person_id: PersonID;
  content: string;
  timestamp?: string;
  token_count?: number;
  message_type: 'person_to_person' | 'system_to_person' | 'person_to_system';
  metadata?: JsonDict;
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

