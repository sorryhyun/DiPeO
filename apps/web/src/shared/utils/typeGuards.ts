import { 
  ApiKey
} from '@/shared/types/core';

// API key type guard
export function isApiKey(value: unknown): value is ApiKey {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value &&
    'service' in value &&
    typeof (value as any).id === 'string' &&
    typeof (value as any).name === 'string' &&
    ['claude', 'openai', 'grok', 'gemini', 'custom'].includes((value as any).service)
  );
}

// Generic array type guard helper
export function isArrayOfType<T>(
  value: unknown,
  typeGuard: (item: unknown) => item is T
): value is T[] {
  return Array.isArray(value) && value.every(typeGuard);
}

export function parseApiArrayResponse<T>(
  data: unknown,
  typeGuard: (item: unknown) => item is T
): T[] {
  if (isArrayOfType(data, typeGuard)) {
    return data;
  }
  if (Array.isArray(data)) {
    return data.filter(typeGuard);
  }
  return [];
}

