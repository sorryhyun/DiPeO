/**
 * Shared LLM domain models
 * These interfaces serve as the single source of truth for LLM-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */


// LLM chat result
export interface ChatResult {
  text: string;
  promptTokens?: number | null;
  completionTokens?: number | null;
  totalTokens?: number | null;
  rawResponse?: any | null;
}

// LLM message types
export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

// LLM provider configuration
export interface LLMProviderConfig {
  modelName: string;
  apiKey: string;
  baseUrl?: string | null;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
}

// Default model configurations by service
export const DEFAULT_MODELS: Record<string, string[]> = {
  openai: ['gpt-4', 'gpt-3.5-turbo'],
  anthropic: ['claude-3-opus-20240229'],
  google: ['gemini-pro'],
  grok: ['grok-1'],
  bedrock: ['anthropic.claude-3-opus-20240229-v1:0'],
  vertex: ['claude-3-opus@20240229'],
  deepseek: ['deepseek-chat']
};

// Utility functions
export function createChatResult(
  text: string,
  promptTokens?: number,
  completionTokens?: number
): ChatResult {
  const totalTokens = (promptTokens || 0) + (completionTokens || 0);
  return {
    text,
    promptTokens: promptTokens ?? null,
    completionTokens: completionTokens ?? null,
    totalTokens: totalTokens > 0 ? totalTokens : null,
    rawResponse: null
  };
}

export function hasUsage(result: ChatResult): boolean {
  return !!(result.promptTokens || result.completionTokens || result.totalTokens);
}

export function getUsageStats(result: ChatResult): Record<string, number> {
  return {
    prompt_tokens: result.promptTokens || 0,
    completion_tokens: result.completionTokens || 0,
    total_tokens: result.totalTokens || 0
  };
}

