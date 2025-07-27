/**
 * Integration service domain models
 * These interfaces and enums define external service integrations
 * Separated from core diagram models for better modularity
 */

import { LLMService, APIServiceType, NotionOperation, ToolType } from './enums.js';
import { TokenUsage } from './execution.js';

// Re-export imported enums for backward compatibility
export { LLMService, APIServiceType, NotionOperation, ToolType };

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

export interface ToolOutput {
  type: ToolType;
  result: WebSearchResult[] | ImageGenerationResult | any;
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