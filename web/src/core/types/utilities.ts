/**
 * ID generation utilities
 */

import { nanoid } from 'nanoid';
import { Vec2, DataType as DomainDataType } from '@dipeo/domain-models';
import {
  nodeId,
  arrowId,
  personId,
  apiKeyId
} from './branded';

import {ApiKeyID, ArrowID, NodeID, PersonID} from '@dipeo/domain-models';

const DEFAULT_ID_LENGTH = 4;
const SHORT_ID_LENGTH = 4;

export function generateId(length: number = DEFAULT_ID_LENGTH): string {
  return nanoid(length);
}

export function generatePrefixedId(
  prefix: string,
  separator: string = '_',
  length: number = DEFAULT_ID_LENGTH
): string {
  return `${prefix}${separator}${nanoid(length)}`;
}





export function generateApiKeyId(): ApiKeyID {
  return apiKeyId(`APIKEY_${nanoid(4).replace(/-/g, '_').toUpperCase()}`);
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


export type Dict<V = unknown> = Record<string, V>;

// Import base DataType from domain models and extend with UI-specific types
export type ExtendedDataType = DomainDataType | 'text' | 'integer' | 'float' | 'json';

// Keep DataType as alias for backward compatibility
export type DataType = ExtendedDataType;