/**
 * Standardized store access hooks following the pattern:
 * - use{Entity}Data - for reading data
 * - use{Entity}Operations - for mutations/actions
 * - use{Entity}State - for computed/derived state
 * 
 * Always use useShallow when selecting multiple properties.
 */

export * from './data';
export * from './operations';
export * from './state';