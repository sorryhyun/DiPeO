import { ApiKeyID } from '../branded';

/**
 * API service types
 */
export type ApiService = 'openai' | 'gemini' | 'claude' | 'grok';

/**
 * Pure domain API key - represents an API key configuration
 */
export interface DomainApiKey {
  id: ApiKeyID;
  service: ApiService;
  label: string;
  key?: string; // Optional - not stored in frontend for security
}

/**
 * Type guard for domain API key
 */
export function isDomainApiKey(obj: unknown): obj is DomainApiKey {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'service' in obj &&
    'label' in obj
  );
}

/**
 * Create a new API key
 */
export function createApiKey(
  id: ApiKeyID,
  service: ApiService,
  label: string,
  key?: string
): DomainApiKey {
  return {
    id,
    service,
    label,
    key
  };
}