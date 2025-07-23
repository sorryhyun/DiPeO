// Auto-generated TypeScript model for api_job node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface Api_jobNodeData {
  url: string;
  method: any;
  headers?: Record<string, any>;
  params?: Record<string, any>;
  body?: Record<string, any>;
  timeout?: number;
  auth_type?: any;
  auth_config?: Record<string, any>;
}

export interface Api_jobNode extends BaseNode {
  type: 'api_job';
  data: Api_jobNodeData;
}

// Zod schema for validation
export const Api_jobNodeDataSchema = z.object({
  url: z.string(),  method: z.any(),  headers: z.record(z.any()).optional(),  params: z.record(z.any()).optional(),  body: z.record(z.any()).optional(),  timeout: z.number().optional(),  auth_type: z.any().optional(),  auth_config: z.record(z.any()).optional()});

export const Api_jobNodeSchema = z.object({
  type: z.literal('api_job'),
  data: Api_jobNodeDataSchema,
});