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
  EXECUTION_CAPABILITIES: '/api/diagrams/execution-capabilities',
  EXECUTION_DETAILS: (id: string) => `/api/executions/${id}`,
  EXECUTION_STATE: (id: string) => `/api/executions/${id}/state`,
  PAUSE_EXECUTION: (id: string) => `/api/executions/${id}/pause`,
  RESUME_EXECUTION: (id: string) => `/api/executions/${id}/resume`,
  HEALTH: '/api/diagrams/health',
  
  // Resource management  
  API_KEYS: '/api/api-keys/',
  API_KEY_BY_ID: (id: string) => `/api/api-keys/${id}`,
  MODELS: (id: string) => `/api/api-keys/${id}/models`,
  INITIALIZE_MODEL: '/api/initialize-model',
  CONVERSATIONS: '/api/conversations',
  
  // File operations
  UPLOAD_FILE: '/api/files/upload',
  
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

// Simple in-memory cache for API responses
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

class ApiCache {
  private cache: Map<string, CacheEntry<unknown>> = new Map();
  private defaultTTL = 5 * 60 * 1000; // 5 minutes default TTL

  set<T>(key: string, data: T, ttl?: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now() + (ttl || this.defaultTTL)
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    // Check if cache is expired
    if (Date.now() > entry.timestamp) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  invalidate(key: string): void {
    this.cache.delete(key);
  }

  invalidateAll(): void {
    this.cache.clear();
  }

  // Generate cache key for model list
  static getModelListKey(service: string, apiKeyId: string): string {
    return `models:${service}:${apiKeyId}`;
  }
}

// Export singleton instance
export const apiCache = new ApiCache();
export { ApiCache };