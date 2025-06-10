import type { DomainApiKey, DomainArrow, DomainHandle, InputHandle, OutputHandle } from './domain';
import type { NodeKind } from './primitives';

/**
 * Type guard to check if an object is an ApiKey
 */
export function isApiKey(obj: unknown): obj is DomainApiKey {
  if (!obj || typeof obj !== 'object') return false;
  const apiKey = obj as Record<string, unknown>;
  return (
    typeof apiKey.id === 'string' &&
    typeof apiKey.name === 'string' &&
    typeof apiKey.service === 'string' &&
    ['openai', 'claude', 'gemini', 'grok'].includes(apiKey.service as string)
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

/**
 * Type guard for domain arrows
 */
export function isDomainArrow(obj: unknown): obj is DomainArrow {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'source' in obj &&
    'target' in obj &&
    typeof (obj as any).source === 'string' &&
    typeof (obj as any).target === 'string' &&
    (obj as any).source.includes(':') &&
    (obj as any).target.includes(':')
  );
}

/**
 * Type guard for domain handles
 */
export function isDomainHandle(obj: unknown): obj is DomainHandle {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'nodeId' in obj &&
    'name' in obj &&
    'direction' in obj &&
    'dataType' in obj
  );
}

/**
 * Type guard for input handles
 */
export function isInputHandle(handle: DomainHandle): handle is InputHandle {
  return handle.direction === 'input';
}

/**
 * Type guard for output handles
 */
export function isOutputHandle(handle: DomainHandle): handle is OutputHandle {
  return handle.direction === 'output';
}

/**
 * Type guard to check if a value is a valid node type
 */
export function isNodeKind(value: unknown): value is NodeKind {
  return typeof value === 'string' && [
    'start',
    'person_job',
    'person_batch_job',
    'condition',
    'db',
    'endpoint',
    'job',
    'notion',
    'user_response'
  ].includes(value);
}