/**
 * Shared person domain models
 * These interfaces serve as the single source of truth for person (LLM agent) related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import { ForgettingMode, type PersonID, type ApiKeyID, type LLMService } from '../diagram';
import { Message, ConversationMetadata, Conversation } from './conversation';

// Re-export person-related types from diagram for convenience
export type { PersonID, LLMService };
export { ForgettingMode };

// Re-export conversation types
export type { Message, Conversation, MemoryConfig, MemoryState } from './conversation';

// Person-specific models (most are already in diagram domain)
export interface PersonConfiguration {
  id: PersonID;
  label: string;
  service: LLMService;
  model: string;
  apiKeyId?: ApiKeyID | null;
  systemPrompt?: string | null;
  forgettingMode: ForgettingMode;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
}

// Export conversation metadata type
export type { ConversationMetadata };

export interface PersonExecutionContext {
  personId: PersonID;
  nodeId: string;
  conversationId?: string;
  forgettingMode: ForgettingMode;
  systemPrompt?: string | null;
  temperature?: number;
  maxTokens?: number;
}


// Utility functions
export function createConversationMessage(
  role: 'system' | 'user' | 'assistant',
  content: string,
  tokenCount?: number
): Message {
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substr(2, 9),
    role,
    content,
    timestamp: new Date().toISOString(),
    tokenCount
  };
}

export function createEmptyConversation(personId: PersonID): Conversation {
  const now = new Date().toISOString();
  return {
    personId,
    messages: [],
    metadata: {
      startedAt: now,
      lastMessageAt: now,
      totalTokens: 0,
      messageCount: 0,
      contextResets: 0
    }
  };
}

export function shouldResetContext(
  forgettingMode: ForgettingMode,
  messageCount: number,
  userRequested: boolean = false
): boolean {
  switch (forgettingMode) {
    case ForgettingMode.NO_FORGET:
      return false;
    case ForgettingMode.ON_EVERY_TURN:
      return messageCount > 0;
    case ForgettingMode.UPON_REQUEST:
      return userRequested;
    default:
      return false;
  }
}

