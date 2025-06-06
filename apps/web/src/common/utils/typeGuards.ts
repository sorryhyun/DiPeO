import { 
  ApiKey
} from '../../types';

// API key type guard
export function isApiKey(value: unknown): value is ApiKey {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value &&
    'service' in value &&
    typeof (value as { id: unknown }).id === 'string' &&
    typeof (value as { name: unknown }).name === 'string' &&
    ['claude', 'openai', 'grok', 'gemini', 'custom'].includes((value as { service: unknown }).service as string)
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

