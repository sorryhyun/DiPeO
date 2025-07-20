/**
 * Integration service domain models
 * These interfaces and enums define external service integrations
 * Separated from core diagram models for better modularity
 */

// LLM Service Providers
export enum LLMService {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  BEDROCK = 'bedrock',
  VERTEX = 'vertex',
  DEEPSEEK = 'deepseek'
}

// All API Service Types (including non-LLM services)
export enum APIServiceType {
  // LLM Services
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  GEMINI = 'gemini',  // Google Gemini specifically
  BEDROCK = 'bedrock',
  VERTEX = 'vertex',
  DEEPSEEK = 'deepseek',
  
  // Other Services
  NOTION = 'notion',
  GOOGLE_SEARCH = 'google_search',
  SLACK = 'slack',
  GITHUB = 'github',
  JIRA = 'jira'
}

// Notion API Operations
export enum NotionOperation {
  CREATE_PAGE = 'create_page',
  UPDATE_PAGE = 'update_page',
  READ_PAGE = 'read_page',
  DELETE_PAGE = 'delete_page',
  CREATE_DATABASE = 'create_database',
  QUERY_DATABASE = 'query_database',
  UPDATE_DATABASE = 'update_database'
}

import { TokenUsage } from './execution.js';

// Tool Types
export enum ToolType {
  WEB_SEARCH = 'web_search',
  WEB_SEARCH_PREVIEW = 'web_search_preview',
  IMAGE_GENERATION = 'image_generation',
  VOICE = 'voice',
  SPEECH_TO_TEXT = 'speech_to_text',
  TEXT_TO_SPEECH = 'text_to_speech',
}

export interface ToolConfig {
  type: ToolType;
  enabled?: boolean;
  config?: Record<string, any>;
}

// Tool Output Types
export interface WebSearchResult {
  url: string;
  title: string;
  snippet: string;
  score?: number;
}

export interface ImageGenerationResult {
  image_data: string; // Base64 encoded image
  format: string; // e.g., 'png', 'jpeg'
  width?: number;
  height?: number;
}

export interface SpeechToTextResult {
  text: string;
  language?: string;
  confidence?: number;
  segments?: Array<{
    text: string;
    start: number;
    end: number;
    confidence?: number;
  }>;
}

export interface TextToSpeechResult {
  audio_data: string; // Base64 encoded audio
  format: string; // e.g., 'mp3', 'wav', 'opus'
  duration?: number; // Duration in seconds
  voice?: string; // Voice ID used
}

export interface ToolOutput {
  type: ToolType;
  result: WebSearchResult[] | ImageGenerationResult | SpeechToTextResult | TextToSpeechResult | any;
  raw_response?: any;
}

// LLM Chat Result
export interface ChatResult {
  text: string;
  token_usage?: TokenUsage | null;
  raw_response?: any | null;
  tool_outputs?: ToolOutput[] | null;
}

// LLM Request Options
export interface LLMRequestOptions {
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  n?: number;
  tools?: ToolConfig[];
  response_format?: any; // For structured outputs
}

// Future: Add more integration-related types here
// e.g., SlackOperation, GitHubOperation, etc.