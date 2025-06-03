// API and LLM service types

export interface ApiKey {
  id: string;
  name: string;
  service: 'claude' | 'openai' | 'grok' | 'gemini' | 'custom';
  keyReference?: string;
}

export enum LLMService {
  OPENAI = 'openai',
  CLAUDE = 'claude',
  GEMINI = 'gemini',
  GROK = 'grok'
}

export interface ChatResult {
  text: string;
  usage?: LLMUsage;
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
  rawResponse?: unknown;
}

export interface LLMUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  cost: number;
}

export interface APIKeyInfo {
  id: string;
  name: string;
  service: LLMService;
  keyReference?: string;
  isValid?: boolean;
  lastUsed?: Date;
}