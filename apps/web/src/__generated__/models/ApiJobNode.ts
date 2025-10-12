// Auto-generated TypeScript model for api_job node
import { z } from 'zod';
import { AuthType, HttpMethod } from '@dipeo/models';

export interface ApiJobNodeData {
  url: string;
  method: HttpMethod;
  headers?: Record<string, any> | undefined;
  params?: Record<string, any> | undefined;
  body?: Record<string, any> | undefined;
  timeout?: number | undefined;
  auth_type?: AuthType | undefined;
  auth_config?: Record<string, any> | undefined;
}

// Zod schema for validation
export const ApiJobNodeDataSchema = z.object({
  url: z.string().describe("API endpoint URL"),
  method: z.any().describe("HTTP method"),
  headers: z.record(z.any()).optional().describe("HTTP headers"),
  params: z.record(z.any()).optional().describe("Query parameters"),
  body: z.record(z.any()).optional().describe("Request body"),
  timeout: z.number().min(0).max(3600).optional().describe("Request timeout in seconds"),
  auth_type: z.any().optional().describe("Authentication type"),
  auth_config: z.record(z.any()).optional().describe("Authentication configuration"),
});
