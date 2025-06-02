/**
 * Central API configuration for all endpoints
 * Provides consistent base URLs and endpoint definitions
 */

// Type declaration for Node.js environment
declare const process: { env: Record<string, string | undefined> } | undefined;

// Determine environment - Vite provides import.meta.env
// In Node.js/CLI environment, import.meta is not available
const isDev = typeof window === 'undefined' ? true : (import.meta?.env?.DEV ?? false);
const apiHost = typeof window === 'undefined' 
  ? (process?.env?.VITE_API_HOST || 'localhost:8000')
  : (import.meta?.env?.VITE_API_HOST || 'localhost:8000');

// Base URLs
export const API_CONFIG = {
  // HTTP API base URL
  BASE_URL: isDev || typeof window === 'undefined' ? `http://${apiHost}` : '',
  
  // SSE streaming base URL
  STREAMING_BASE_URL: isDev || typeof window === 'undefined' ? `http://${apiHost}` : '',
} as const;

// Export for backward compatibility
export const API_BASE_URL = API_CONFIG.BASE_URL;

// API Endpoints - Standardized with consistent kebab-case and logical grouping
export const API_ENDPOINTS = {
  // Diagram execution
  RUN_DIAGRAM: '/api/run-diagram',
  RUN_DIAGRAM_SYNC: '/api/run-diagram-sync',
  STREAMING_RUN: '/api/stream/run-diagram',
  
  // Resource management  
  API_KEYS: '/api/keys',
  API_KEY_BY_ID: (id: string) => `/api/keys/${id}`,
  MODELS: '/api/models',
  INITIALIZE_MODEL: '/api/initialize-model',
  CONVERSATIONS: '/api/conversations',
  
  // File operations
  UPLOAD_FILE: '/api/upload-file',
  
  // Import/Export
  IMPORT_UML: '/api/import-uml',
  IMPORT_YAML: '/api/import-yaml', 
  SAVE_DIAGRAM: '/api/save',
  EXPORT_UML: '/api/export-uml',
  
  // Monitoring
  MONITOR_STREAM: '/api/monitor/stream',
} as const;

// Helper functions
export function getApiUrl(endpoint: string): string {
  // In Node.js/CLI environment, always use full URL
  if (typeof window === 'undefined') {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
  }
  
  // In browser with dev server proxy, relative paths work
  if (endpoint.startsWith('/api')) {
    return endpoint;
  }
  
  // For other paths, prepend base URL
  return `${API_CONFIG.BASE_URL}${endpoint}`;
}

export function getStreamingUrl(endpoint: string): string {
  return `${API_CONFIG.STREAMING_BASE_URL}${endpoint}`;
}

