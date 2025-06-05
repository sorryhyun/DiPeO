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
} as const;

// Export for backward compatibility
export const API_BASE_URL = API_CONFIG.BASE_URL;

// API Endpoints - Standardized with consistent kebab-case and logical grouping
export const API_ENDPOINTS = {
  // Diagram execution (Unified Backend)
  RUN_DIAGRAM: '/api/diagrams/execute',
  EXECUTION_CAPABILITIES: '/api/execution-capabilities',
  EXECUTION_DETAILS: (id: string) => `/api/executions/${id}`,
  EXECUTION_STATE: (id: string) => `/api/executions/${id}/state`,
  PAUSE_EXECUTION: (id: string) => `/api/executions/${id}/pause`,
  RESUME_EXECUTION: (id: string) => `/api/executions/${id}/resume`,
  HEALTH: '/api/health',
  
  // Resource management  
  API_KEYS: '/api/api-keys/',
  API_KEY_BY_ID: (id: string) => `/api/api-keys/${id}`,
  MODELS: (id: string) => `/api/api-keys/${id}/models`,
  INITIALIZE_MODEL: '/api/initialize-model',
  CONVERSATIONS: '/api/conversations',
  
  // File operations
  UPLOAD_FILE: '/api/upload-file',
  
  // Import/Export
  IMPORT_YAML: '/api/import-yaml', 
  SAVE_DIAGRAM: '/api/diagrams/save',
  DIAGRAMS_CONVERT: '/api/diagrams/convert',
  
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

