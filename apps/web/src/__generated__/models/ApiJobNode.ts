







// Auto-generated TypeScript model for api_job node
import { z } from 'zod';

export interface ApiJobNodeData {
  url: string;
  method: enum;
  headers?: Record<string, any>;
  params?: Record<string, any>;
  body?: Record<string, any>;
  timeout?: number;
  auth_type?: enum;
  auth_config?: Record<string, any>;
}

// Zod schema for validation
export const ApiJobNodeDataSchema = z.object({
  url: z.string(),
  method: z.any(),
  headers: z.record(z.any()).optional(),
  params: z.record(z.any()).optional(),
  body: z.record(z.any()).optional(),
  timeout: z.number().optional(),
  auth_type: z.any().optional(),
  auth_config: z.record(z.any()).optional(),
});