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
  url: stringSchema,  method: enumSchema,  headers: objectSchema.optional(),  params: objectSchema.optional(),  body: objectSchema.optional(),  timeout: numberSchema.optional(),  auth_type: enumSchema.optional(),  auth_config: objectSchema.optional()});

export const Api_jobNodeSchema = z.object({
  type: z.literal('api_job'),
  data: Api_jobNodeDataSchema,
});