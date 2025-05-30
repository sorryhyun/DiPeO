/**
 * Central API configuration for all endpoints
 * Provides consistent base URLs and endpoint definitions
 */

// Determine environment
const isDev = import.meta.env.DEV;
const apiHost = import.meta.env.VITE_API_HOST || 'localhost:8000';

// Base URLs
export const API_CONFIG = {
  // HTTP API base URL
  BASE_URL: isDev ? `http://${apiHost}` : '',
  
  // SSE streaming base URL
  STREAMING_BASE_URL: isDev ? `http://${apiHost}` : '',
  
  // WebSocket base URL (to be deprecated)
  WS_BASE_URL: isDev ? `ws://${apiHost}` : `ws://${window.location.host}`,
} as const;

// API Endpoints
export const API_ENDPOINTS = {
  // Diagram execution
  RUN_DIAGRAM: '/api/run-diagram',
  STREAMING_RUN: '/api/stream/run-diagram',
  
  // API Keys
  API_KEYS: '/api/api-keys',
  API_KEY_BY_ID: (id: string) => `/api/api-keys/${id}`,
  
  // File operations
  UPLOAD_FILE: '/api/upload-file',
  
  // Models
  MODELS: '/api/models',
  
  // Conversations
  CONVERSATIONS: '/api/conversations',

  MONITOR_STREAM: '/api/monitor/stream',
} as const;

// Helper functions
export function getApiUrl(endpoint: string): string {
  // For relative paths starting with /api, no base URL needed (uses proxy)
  if (endpoint.startsWith('/api')) {
    return endpoint;
  }
  // For other paths, prepend base URL
  return `${API_CONFIG.BASE_URL}${endpoint}`;
}

export function getStreamingUrl(endpoint: string): string {
  return `${API_CONFIG.STREAMING_BASE_URL}${endpoint}`;
}

