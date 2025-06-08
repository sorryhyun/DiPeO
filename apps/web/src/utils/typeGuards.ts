import type { ApiKey } from '@/types';

/**
 * Type guard to check if an object is an ApiKey
 */
export function isApiKey(obj: unknown): obj is ApiKey {
  if (!obj || typeof obj !== 'object') return false;
  const apiKey = obj as Record<string, unknown>;
  return (
    typeof apiKey.id === 'string' &&
    typeof apiKey.name === 'string' &&
    typeof apiKey.service === 'string' &&
    ['openai', 'claude', 'google', 'grok'].includes(apiKey.service as string)
  );
}

/**
 * Parse API array response with type guard
 */
export function parseApiArrayResponse<T>(
  data: unknown,
  typeGuard: (item: unknown) => item is T
): T[] {
  if (!Array.isArray(data)) return [];
  return data.filter(typeGuard);
}