/**
 * Centralized conversion service for transforming between different type representations
 * Consolidates all type conversion logic in one place
 */

import { NodeConverter } from './converters/node-converter';
import { ArrowConverter } from './converters/arrow-converter';
import { HandleConverter } from './converters/handle-converter';
import { DiagramConverter } from './converters/diagram-converter';
import { ExecutionConverter } from './converters/execution-converter';
import { PersonConverter } from './converters/person-converter';

// Export the main ConversionService (moved from core/services)
export { Converters } from './ConversionService';

// Re-export all individual converters from a single location
export const IndividualConverters = {
  node: NodeConverter,
  arrow: ArrowConverter,
  handle: HandleConverter,
  diagram: DiagramConverter,
  execution: ExecutionConverter,
  person: PersonConverter,
} as const;

// Export individual converters for backwards compatibility
export { NodeConverter } from './converters/node-converter';
export { ArrowConverter } from './converters/arrow-converter';
export { HandleConverter } from './converters/handle-converter';
export { DiagramConverter } from './converters/diagram-converter';
export { ExecutionConverter } from './converters/execution-converter';
export { PersonConverter } from './converters/person-converter';

// Type exports
export type * from './converters/node-converter';
export type * from './converters/arrow-converter';
export type * from './converters/handle-converter';
export type * from './converters/diagram-converter';
export type * from './converters/execution-converter';
export type * from './converters/person-converter';