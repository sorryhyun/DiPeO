// Auto-generated TypeScript model for integrated_api node
import { z } from 'zod';

export interface IntegratedApiNodeData {
  provider: string;
  operation: string;
  resource_id?: string;
  config?: Record<string, any>;
  timeout?: number;
  max_retries?: number;
}

// Zod schema for validation
export const IntegratedApiNodeDataSchema = z.object({
  provider: z.string(),
  operation: z.string(),
  resource_id: z.string().optional(),
  config: z.record(z.any()).optional(),
  timeout: z.number().min(1).max(300).optional(),
  max_retries: z.number().min(0).max(10).optional(),
});