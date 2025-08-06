/**
 * Integration service domain models
 * These interfaces and enums define external service integrations
 * Separated from core diagram models for better modularity
 */

import { LLMService, APIServiceType, ToolType } from './enums/integrations.js';
import { NotionOperation } from './enums/node-specific.js';
import { TokenUsage } from './execution.js';

export { LLMService, APIServiceType, ToolType, NotionOperation };

export interface ToolConfig {
  type: ToolType;
  enabled?: boolean;
  config?: Record<string, any>;
}

export interface WebSearchResult {
  url: string;
  title: string;
  snippet: string;
  score?: number;
}

export interface ImageGenerationResult {
  image_data: string;
  format: string;
  width?: number;
  height?: number;
}

export interface ToolOutput {
  type: ToolType;
  result: WebSearchResult[] | ImageGenerationResult | any;
  raw_response?: any;
}


export interface ChatResult {
  text: string;
  token_usage?: TokenUsage | null;
  raw_response?: any | null;
  tool_outputs?: ToolOutput[] | null;
}

export interface LLMRequestOptions {
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  n?: number;
  tools?: ToolConfig[];
  response_format?: any;
}

