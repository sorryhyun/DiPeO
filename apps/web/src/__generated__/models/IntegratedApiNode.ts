// Auto-generated TypeScript model for integrated_api node
import { z } from 'zod';
import { PersonID } from '@dipeo/models';

export interface IntegratedApiNodeData {
  provider: string;
  operation: string;
  resource_id?: string | undefined;
  config?: Record<string, any> | undefined;
  timeout?: number | undefined;
  max_retries?: number | undefined;
}

// Zod schema for validation
export const IntegratedApiNodeDataSchema = z.object({
  provider: z.string().describe("API provider to connect to"),
  operation: z.string().describe("Operation to perform (provider-specific)"),
  resource_id: z.string().optional().describe("Resource identifier (e.g., page ID, channel ID)"),
  config: z.record(z.any()).optional().describe("Provider-specific configuration"),
  timeout: z.number().min(1).max(300).optional().describe("Request timeout in seconds"),
  max_retries: z.number().min(0).max(10).optional().describe("Maximum retry attempts"),
});
