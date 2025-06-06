// API types - Request/response interfaces, WebSocket messages, and execution client types

// Base API Response
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  filename?: string;
  path?: string;
}

// API Client Configuration
export interface ApiClientOptions {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  timeout?: number;
}

// WebSocket Types
export interface WSMessage {
  type: string;
  [key: string]: any;
}

export interface MessageHandler {
  (message: WSMessage): void;
}

export interface ConnectionHandler {
  (): void;
}

export interface WebSocketClientOptions {
  url?: string;
  protocols?: string[];
  onOpen?: ConnectionHandler;
  onClose?: ConnectionHandler;
  onError?: (error: Event) => void;
  onMessage?: MessageHandler;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  reconnectDecay?: number;
  maxReconnectAttempts?: number;
  debug?: boolean;
}

// Execution Client Types
export interface DiagramData {
  nodes: any[];
  arrows: any[];
  persons: any[];
  apiKeys: any[];
  metadata?: Record<string, any>;
}

export interface ExecutionOptions {
  mode?: 'monitor' | 'headless' | 'check';
  debug?: boolean;
  delay?: number;
  continueOnError?: boolean;
  allowPartial?: boolean;
  debugMode?: boolean;
}

export interface ExecutionUpdate {
  type: string;
  executionId?: string;
  nodeId?: string;
  nodeType?: string;
  output?: unknown;
  output_preview?: string;
  context?: Record<string, unknown>;
  totalCost?: number;
  cost?: number;
  error?: string;
  timestamp?: string;
  conversationId?: string;
  message?: unknown;
  status?: string;
}

export interface ExecutionResult {
  success?: boolean;
  executionId?: string;
  context?: Record<string, unknown>;
  totalCost?: number;
  duration?: number;
  finalContext?: Record<string, any>;
  error?: string;
  metadata?: {
    totalCost?: number;
    executionTime?: number;
  };
}

// API Endpoints
export interface DiagramSaveRequest {
  diagram: DiagramData;
  filename?: string;
  format?: 'json' | 'yaml' | 'llm-yaml';
}

export interface DiagramSaveResponse {
  success: boolean;
  filename: string;
  path: string;
  message?: string;
}

export interface ConvertRequest {
  content: string;
  from: 'json' | 'yaml' | 'llm-yaml';
  to: 'json' | 'yaml' | 'llm-yaml';
}

export interface ConvertResponse {
  success: boolean;
  converted: string;
  error?: string;
}

// Health Check Response
export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version?: string;
  uptime?: number;
}

// Execution Capabilities Response
export interface ExecutionCapabilitiesResponse {
  supportedNodeTypes: string[];
  features: {
    realTimeControl: boolean;
    interactivePrompts: boolean;
    persistentMemory: boolean;
    monitoring: boolean;
  };
  version: string;
}