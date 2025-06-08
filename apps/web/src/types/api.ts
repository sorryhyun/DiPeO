// types/api.ts - API layer types

import type { Dict, ID } from './primitives';
import type { Diagram } from './diagram';

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RequestConfig<B = unknown, Q = Dict, H extends Dict<string> = Dict<string>> {
  url: string;
  method?: HttpMethod;
  body?: B;
  query?: Q;
  headers?: H;
  signal?: AbortSignal;
}

interface ApiMeta { filename?: string; path?: string }

export type ApiResponse<T = unknown> =
  | ({ success: true; data: T } & ApiMeta)
  | ({ success: false; error: string } & ApiMeta);

export interface ApiClientOptions {
  baseURL?: string;
  timeout?: number;
  headers?: Dict<string>;
}

// API Request/Response types
export interface DiagramSaveRequest {
  diagram: Diagram;
  filename?: string;
}

export interface DiagramSaveResponse {
  message: string;
  filename: string;
  path: string;
}

export interface ConvertRequest {
  content: string;
  sourceFormat: 'json' | 'yaml' | 'llm-yaml';
  targetFormat: 'json' | 'yaml' | 'llm-yaml';
}

export interface ConvertResponse {
  converted: string;
  format: string;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  version?: string;
  timestamp?: string;
}

export interface ExecutionCapabilitiesResponse {
  node_types: string[];
  features: {
    real_time_control: boolean;
    interactive_prompts: boolean;
    memory_support: boolean;
    forgetting_rules: boolean;
  };
  supported_languages?: string[];
}