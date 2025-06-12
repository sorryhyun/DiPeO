/**
 * Refactored Type Guards using Factory Pattern
 * 
 * Uses the type guard factory to reduce duplication and
 * improve maintainability of runtime type checks.
 */

import {
  createTypeGuard,
  createEnumGuard,
  createBrandedTypeGuard,
  createCollectionGuard,
  isString
} from '@/utils/typeGuardFactory';

import type { 
  DomainApiKey, 
  DomainArrow, 
  DomainHandle, 
  HandleDirection,
  InputHandle, 
  OutputHandle,
  DomainNode,
  DomainPerson,
  ApiService,
  LLMService
} from './domain';
import type { NodeKind } from './primitives';
import type { NodeID, HandleID, ArrowID, PersonID, ApiKeyID } from './branded';

// API Services
const API_SERVICES: readonly ApiService[] = ['openai', 'gemini', 'claude', 'grok'];
const LLM_SERVICES: readonly LLMService[] = ['openai', 'claude', 'gemini', 'grok'];

// Node Kinds
const NODE_KINDS: readonly NodeKind[] = [
  'start',
  'person_job',
  'person_batch_job',
  'condition',
  'db',
  'endpoint',
  'job',
  'notion',
  'user_response'
];

// Handle Directions
const HANDLE_DIRECTIONS: readonly HandleDirection[] = ['input', 'output'];

/**
 * Type guard for API keys using factory
 */
export const isApiKey = createTypeGuard<DomainApiKey>({
  properties: [
    { key: 'id', type: 'string' },
    { key: 'label', type: 'string' },
    { key: 'service', type: 'string', enum: API_SERVICES }
  ]
});

/**
 * Type guard for domain arrows using factory
 */
export const isDomainArrow = createTypeGuard<DomainArrow>({
  properties: [
    { key: 'id', type: 'string' },
    { key: 'source', type: 'string', validator: (v) => String(v).includes(':') },
    { key: 'target', type: 'string', validator: (v) => String(v).includes(':') }
  ]
});

/**
 * Type guard for domain handles using factory
 */
export const isDomainHandle = createTypeGuard<DomainHandle>({
  properties: [
    { key: 'id', type: 'string' },
    { key: 'nodeId', type: 'string' },
    { key: 'name', type: 'string' },
    { key: 'direction', type: 'string', enum: HANDLE_DIRECTIONS },
    { key: 'dataType', type: 'string' }
  ]
});

// Note: isDomainNode and isDomainPerson are already exported from domain module
// We import them here for use in collection guards but don't re-export to avoid conflicts
import { isDomainNode, isDomainPerson } from './domain';

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

// Enum guards using factory
export const isNodeKind = createEnumGuard(NODE_KINDS);
export const isApiService = createEnumGuard(API_SERVICES);
export const isLLMService = createEnumGuard(LLM_SERVICES);
export const isHandleDirection = createEnumGuard(HANDLE_DIRECTIONS);

// Branded type guards using factory
export const isNodeId = createBrandedTypeGuard<NodeID>(
  (value) => /^[a-zA-Z0-9_-]+$/.test(value || '')
);

export const isHandleId = createBrandedTypeGuard<HandleID>(
  (value) => {
    if (!value) return false;
    const parts = value.split(':');
    return parts.length === 2 && 
           /^[a-zA-Z0-9_-]+$/.test(parts[0] || '') &&
           /^[a-zA-Z0-9_-]+$/.test(parts[1] || '');
  }
);

export const isArrowId = createBrandedTypeGuard<ArrowID>(
  (value) => /^arrow_[a-zA-Z0-9_-]+$/.test(value || '')
);

export const isPersonId = createBrandedTypeGuard<PersonID>(
  (value) => /^person_[a-zA-Z0-9_-]+$/.test(value || '')
);

export const isApiKeyId = createBrandedTypeGuard<ApiKeyID>(
  (value) => /^APIKEY_[a-zA-Z0-9]+$/.test(value || '')
);

// Collection guards
export const isApiKeyArray = createCollectionGuard(isApiKey);
export const isDomainNodeArray = createCollectionGuard(isDomainNode);
export const isDomainArrowArray = createCollectionGuard(isDomainArrow);
export const isDomainHandleArray = createCollectionGuard(isDomainHandle);
export const isDomainPersonArray = createCollectionGuard(isDomainPerson);

// Parse helpers
export function parseApiArrayResponse<T>(
  data: unknown,
  typeGuard: (item: unknown) => item is T
): T[] {
  if (!Array.isArray(data)) return [];
  return data.filter(typeGuard);
}

// Complex shape guards for common patterns
export const isPosition = createTypeGuard<{ x: number; y: number }>({
  properties: [
    { key: 'x', type: 'number' },
    { key: 'y', type: 'number' }
  ]
});

export const isSize = createTypeGuard<{ width: number; height: number }>({
  properties: [
    { key: 'width', type: 'number' },
    { key: 'height', type: 'number' }
  ]
});

export const isRect = createTypeGuard<{ x: number; y: number; width: number; height: number }>({
  properties: [
    { key: 'x', type: 'number' },
    { key: 'y', type: 'number' },
    { key: 'width', type: 'number' },
    { key: 'height', type: 'number' }
  ]
});

// Export convenience type
export type AnyDomainEntity = DomainNode | DomainArrow | DomainHandle | DomainPerson | DomainApiKey;

/**
 * Universal entity type guard
 */
export function isDomainEntity(obj: unknown): obj is AnyDomainEntity {
  return isDomainNode(obj) || 
         isDomainArrow(obj) || 
         isDomainHandle(obj) || 
         isDomainPerson(obj) || 
         isApiKey(obj);
}