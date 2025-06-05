// API and LLM service types

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  filename?: string;
  path?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  service: 'claude' | 'openai' | 'grok' | 'gemini' | 'custom';
}

export interface ChatResult {
  text: string;
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
}