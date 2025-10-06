/**
 * Integration service domain models
 * These interfaces and enums define external service integrations
 * Separated from core diagram models for better modularity
 */

import { LLMService, APIServiceType, ToolType } from './enums/integrations.js';
import { LLMUsage } from './execution.js';

export { LLMService, APIServiceType, ToolType };

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
  llm_usage?: LLMUsage | null;
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

// API Provider Types
export interface AuthConfig {
  strategy: string;
  header?: string | null;
  query_param?: string | null;
  format?: string | null;
  scopes?: string[] | null;
}

export interface RateLimitConfig {
  algorithm: string;
  capacity: number;
  refill_per_sec: number;
  window_size_sec?: number | null;
}

export interface RetryPolicy {
  strategy: string;
  max_retries: number;
  base_delay_ms: number;
  max_delay_ms?: number | null;
  retry_on_status: number[];
}

export interface Operation {
  name: string;
  method: string;
  path: string;
  description?: string | null;
  required_scopes?: string[] | null;
  has_pagination: boolean;
  timeout_override?: number | null;
}

export interface OperationSchema {
  operation: string;
  method: string;
  path: string;
  description?: string | null;
  request_body?: any | null;
  query_params?: any | null;
  response?: any | null;
}

export interface ProviderMetadata {
  version: string;
  type: string;
  manifest_path?: string | null;
  description?: string | null;
  documentation_url?: string | null;
  support_email?: string | null;
}

export interface Provider {
  name: string;
  operations: Operation[];
  metadata: ProviderMetadata;
  base_url?: string | null;
  auth_config?: AuthConfig | null;
  rate_limit?: RateLimitConfig | null;
  retry_policy?: RetryPolicy | null;
  default_timeout: number;
}

export interface ProviderStatistics {
  total_providers: number;
  total_operations: number;
  provider_types: any;
  providers: any;
}

export interface IntegrationTestResult {
  success: boolean;
  provider: string;
  operation: string;
  status_code?: number | null;
  response_time_ms?: number | null;
  error?: string | null;
  response_preview?: any | null;
}
