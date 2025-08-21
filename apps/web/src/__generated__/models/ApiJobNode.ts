// Auto-generated TypeScript model for api_job node
import { z } from 'zod';

export interface ApiJobNodeData {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, any>;
  params?: Record<string, any>;
  body?: Record<string, any>;
  timeout?: number;
  auth_type?: 'none' | 'bearer' | 'basic' | 'api_key';
  auth_config?: Record<string, any>;
}

// Zod schema for validation
export const ApiJobNodeDataSchema = z.object({
  url: z.string(),
  method: z.enum(["GET", "POST", "PUT", "DELETE", "PATCH"]),
  headers: z.record(z.any()).optional(),
  params: z.record(z.any()).optional(),
  body: z.record(z.any()).optional(),
  timeout: z.number().optional(),
  auth_type: z.enum(["none", "bearer", "basic", "api_key"]).optional(),
  auth_config: z.record(z.any()).optional(),
});