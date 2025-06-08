import { nanoid } from 'nanoid';
import { 
  NodeID, 
  ArrowID, 
  PersonID, 
  nodeId, 
  arrowId, 
  personId 
} from '@/types/branded';

const DEFAULT_ID_LENGTH = 4;
const SHORT_ID_LENGTH = 4;

export function generateId(length: number = DEFAULT_ID_LENGTH): string {
  return nanoid(length);
}

export function generateShortId(): string {
  return nanoid(SHORT_ID_LENGTH);
}

export function generatePrefixedId(
  prefix: string,
  separator: string = '_',
  length: number = DEFAULT_ID_LENGTH
): string {
  return `${prefix}${separator}${nanoid(length)}`;
}

/**
 * Generate a timestamped ID
 * 
 * Useful for sortable IDs where creation order matters
 * 
 * @param includeRandom - Whether to include random suffix for uniqueness (default: true)
 * @returns A timestamped identifier
 * 
 * @example
 * generateTimestampId() // '1703123456789_V1StGXR8'
 * generateTimestampId(false) // '1703123456789'
 */
export function generateTimestampId(includeRandom: boolean = true): string {
  const timestamp = Date.now().toString();
  return includeRandom ? `${timestamp}_${generateShortId()}` : timestamp;
}

/**
 * Check if a string is a valid nanoid
 * 
 * @param id - The string to check
 * @param expectedLength - Optional expected length to validate
 * @returns Whether the string appears to be a valid nanoid
 */
export function isValidId(id: string, expectedLength?: number): boolean {
  if (!id || typeof id !== 'string') return false;
  
  // Check if it only contains URL-safe characters (nanoid alphabet)
  const nanoIdRegex = /^[A-Za-z0-9_-]+$/;
  if (!nanoIdRegex.test(id)) return false;
  
  // Check length if specified
  if (expectedLength !== undefined && id.length !== expectedLength) return false;
  
  return true;
}

/**
 * Extract prefix from a prefixed ID
 * 
 * @param id - The prefixed ID
 * @param separator - The separator used (default: '_')
 * @returns The prefix or null if not found
 * 
 * @example
 * extractPrefix('node_V1StGXR8') // 'node'
 * extractPrefix('arrow-V1StGXR8', '-') // 'arrow'
 */
export function extractPrefix(id: string, separator: string = '_'): string | null {
  if (!id || !id.includes(separator)) return null;
  const parts = id.split(separator);
  return parts.length > 0 && parts[0] !== undefined ? parts[0] : null;
}


export function generateApiKeyId(): string {
  return `APIKEY_${nanoid(4).replace(/-/g, '_').toUpperCase()}`;
}

/**
 * Generate branded node ID
 */
export function generateNodeId(): NodeID {
  return nodeId(generatePrefixedId('node'));
}

/**
 * Generate branded arrow ID
 */
export function generateArrowId(): ArrowID {
  return arrowId(generatePrefixedId('arrow'));
}

/**
 * Generate branded person ID
 */
export function generatePersonId(): PersonID {
  return personId(generatePrefixedId('person'));
}

/**
 * Type-safe ID generation for specific entity types
 */
export const entityIdGenerators = {
  node: generateNodeId,
  arrow: generateArrowId,
  person: generatePersonId,
  apiKey: () => generateApiKeyId(), // Use custom format
  execution: () => generatePrefixedId('exec'),
  conversation: () => generatePrefixedId('conv'),
} as const;

/**
 * Batch ID generation
 * 
 * Generate multiple unique IDs at once, guaranteed to be unique
 * 
 * @param count - Number of IDs to generate
 * @param options - Optional configuration
 * @returns Array of unique IDs
 */
export function generateBatchIds(
  count: number,
  options?: {
    prefix?: string;
    separator?: string;
    length?: number;
  }
): string[] {
  const ids = new Set<string>();
  const { prefix, separator = '_', length = DEFAULT_ID_LENGTH } = options || {};
  
  while (ids.size < count) {
    const id = prefix 
      ? generatePrefixedId(prefix, separator, length)
      : generateId(length);
    ids.add(id);
  }
  
  return Array.from(ids);
}

// Re-export nanoid for advanced use cases
export { nanoid };