/**
 * Centralized Converter Modules
 * 
 * These modules provide structured conversion functions organized by domain.
 * Each converter module handles bidirectional transformations between:
 * - GraphQL types (from API)
 * - Domain types (from @dipeo/models)
 * - Store types (optimized for Zustand)
 * - UI types (for React components)
 */

export * from './node-converter';
export * from './arrow-converter';
export * from './handle-converter';
export * from './person-converter';
export * from './diagram-converter';
export * from './execution-converter';
export { Converters } from './ConversionService';