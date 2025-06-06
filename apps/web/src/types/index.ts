// Consolidated type exports - avoid duplicate exports
export * from './core';
export * from './runtime';
export * from './ui';

// Only export non-conflicting API types
export {
  type ApiClientOptions,
  type RequestConfig,
  type DiagramSaveRequest,
  type DiagramSaveResponse,
  type ConvertRequest,
  type ConvertResponse,
  type HealthResponse,
  type ExecutionCapabilitiesResponse
} from './api';

// Re-export simplified node configurations
export { NODE_CONFIGS } from '@/config';

// Alias for backward compatibility
export { NODE_CONFIGS as UNIFIED_NODE_CONFIGS } from '@/config';