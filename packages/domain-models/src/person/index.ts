/**
 * Shared person domain models
 * These interfaces serve as the single source of truth for person (LLM agent) related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import { z } from 'zod';
import { ForgettingMode, type PersonID, type ApiKeyID, type LLMService } from '../diagram';

// Re-export person-related types from diagram for convenience
export type { PersonID, LLMService };
export { ForgettingMode };

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

export interface PersonConversation {
  personId: PersonID;
  messages: ConversationMessage[];
  metadata?: ConversationMetadata;
}

export interface ConversationMessage {
  id: string;
  role: 'system' | 'user' | 'assistant';
  content: string;
  timestamp: string; // ISO datetime string
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

export interface PersonExecutionContext {
  personId: PersonID;
  nodeId: string;
  conversationId?: string;
  forgettingMode: ForgettingMode;
  systemPrompt?: string | null;
  temperature?: number;
  maxTokens?: number;
}

// Zod schemas for validation
export const PersonConfigurationSchema = z.object({
  id: z.string(),
  label: z.string(),
  service: z.string(),
  model: z.string(),
  apiKeyId: z.string().nullable().optional(),
  systemPrompt: z.string().nullable().optional(),
  forgettingMode: z.string(),
  temperature: z.number().optional(),
  maxTokens: z.number().optional(),
  topP: z.number().optional(),
  frequencyPenalty: z.number().optional(),
  presencePenalty: z.number().optional()
});

export const ConversationMessageSchema = z.object({
  id: z.string(),
  role: z.enum(['system', 'user', 'assistant']),
  content: z.string(),
  timestamp: z.string(),
  tokenCount: z.number().optional(),
  metadata: z.record(z.any()).optional()
});

export const ConversationMetadataSchema = z.object({
  startedAt: z.string(),
  lastMessageAt: z.string(),
  totalTokens: z.number(),
  messageCount: z.number(),
  contextResets: z.number()
});

export const PersonConversationSchema = z.object({
  personId: z.string(),
  messages: z.array(ConversationMessageSchema),
  metadata: ConversationMetadataSchema.optional()
});

export const PersonExecutionContextSchema = z.object({
  personId: z.string(),
  nodeId: z.string(),
  conversationId: z.string().optional(),
  forgettingMode: z.string(),
  systemPrompt: z.string().nullable().optional(),
  temperature: z.number().optional(),
  maxTokens: z.number().optional()
});

// Utility functions
export function createConversationMessage(
  role: 'system' | 'user' | 'assistant',
  content: string,
  tokenCount?: number
): ConversationMessage {
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substr(2, 9),
    role,
    content,
    timestamp: new Date().toISOString(),
    tokenCount
  };
}

export function createEmptyConversation(personId: PersonID): PersonConversation {
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

// Type guards
export function isPersonConfiguration(obj: unknown): obj is PersonConfiguration {
  return PersonConfigurationSchema.safeParse(obj).success;
}

export function isPersonConversation(obj: unknown): obj is PersonConversation {
  return PersonConversationSchema.safeParse(obj).success;
}

export function isConversationMessage(obj: unknown): obj is ConversationMessage {
  return ConversationMessageSchema.safeParse(obj).success;
}