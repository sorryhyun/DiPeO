/**
 * Centralized ID generation utilities
 * 
 * Provides consistent ID generation across the application
 * using nanoid for URL-safe unique identifiers.
 */

import { nanoid } from 'nanoid';

/**
 * Default ID length for general use
 */
const DEFAULT_ID_LENGTH = 21;

/**
 * Shorter ID length for human-readable IDs
 */
const SHORT_ID_LENGTH = 10;

/**
 * Generate a unique ID
 * 
 * @param length - Optional length of the ID (default: 21)
 * @returns A URL-safe unique identifier
 */
export function generateId(length: number = DEFAULT_ID_LENGTH): string {
  return nanoid(length);
}

/**
 * Generate a short unique ID (10 characters)
 * 
 * Use this for user-visible IDs where brevity is important.
 * Note: Shorter IDs have higher collision probability.
 * 
 * @returns A short URL-safe unique identifier
 */
export function generateShortId(): string {
  return nanoid(SHORT_ID_LENGTH);
}

/**
 * Generate a prefixed ID
 * 
 * Useful for type-safe IDs that indicate their purpose
 * 
 * @param prefix - The prefix to add (e.g., 'node', 'arrow', 'person')
 * @param separator - Optional separator between prefix and ID (default: '_')
 * @param length - Optional length of the random part (default: 21)
 * @returns A prefixed unique identifier
 * 
 * @example
 * generatePrefixedId('node') // 'node_V1StGXR8_Z5jdHi6B-myT'
 * generatePrefixedId('arrow', '-') // 'arrow-V1StGXR8_Z5jdHi6B-myT'
 */
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

/**
 * Type-safe ID generation for specific entity types
 */
export const entityIdGenerators = {
  node: () => generatePrefixedId('node'),
  arrow: () => generatePrefixedId('arrow'),
  person: () => generatePrefixedId('person'),
  apiKey: () => generatePrefixedId('apikey'),
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