/**
 * Utility functions for working with service types
 * These utilities help distinguish between LLM and non-LLM services
 */

import { LLMService, APIServiceType } from './integration.js';

/**
 * Set of APIServiceType values that are LLM services
 */
const LLM_SERVICE_TYPES = new Set<APIServiceType>([
  APIServiceType.OPENAI,
  APIServiceType.ANTHROPIC,
  APIServiceType.GOOGLE,
  APIServiceType.GEMINI,
  APIServiceType.BEDROCK,
  APIServiceType.VERTEX,
  APIServiceType.DEEPSEEK,
]);

/**
 * Check if an APIServiceType is an LLM service
 */
export function isLLMService(service: APIServiceType): boolean {
  return LLM_SERVICE_TYPES.has(service);
}

/**
 * Convert APIServiceType to LLMService
 * @throws Error if the APIServiceType is not an LLM service
 */
export function apiServiceTypeToLLMService(service: APIServiceType): LLMService {
  if (!isLLMService(service)) {
    throw new Error(`APIServiceType "${service}" is not an LLM service`);
  }
  
  // Handle special cases
  if (service === APIServiceType.GEMINI) {
    return LLMService.GOOGLE;
  }
  
  // Direct mapping for others
  return service as unknown as LLMService;
}

/**
 * Convert LLMService to APIServiceType
 */
export function llmServiceToAPIServiceType(service: LLMService): APIServiceType {
  // Direct mapping works for all LLMService values
  return service as unknown as APIServiceType;
}

/**
 * Get all LLM service types
 */
export function getLLMServiceTypes(): APIServiceType[] {
  return Array.from(LLM_SERVICE_TYPES);
}

/**
 * Get all non-LLM service types
 */
export function getNonLLMServiceTypes(): APIServiceType[] {
  return Object.values(APIServiceType).filter(service => !isLLMService(service));
}

/**
 * Type guard to check if a string is a valid LLMService
 */
export function isValidLLMService(service: string): service is LLMService {
  return Object.values(LLMService).includes(service as LLMService);
}

/**
 * Type guard to check if a string is a valid APIServiceType
 */
export function isValidAPIServiceType(service: string): service is APIServiceType {
  return Object.values(APIServiceType).includes(service as APIServiceType);
}