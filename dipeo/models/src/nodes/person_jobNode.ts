// Auto-generated TypeScript model for person_job node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface Person_jobNodeData {
  person?: string;
  first_only_prompt: string;
  default_prompt?: string;
  max_iteration: number;
  memory_config?: Record<string, any>;
  memory_settings?: Record<string, any>;
  tools?: any[];
}

export interface Person_jobNode extends BaseNode {
  type: 'person_job';
  data: Person_jobNodeData;
}

// Zod schema for validation
export const Person_jobNodeDataSchema = z.object({
  person: z.string().optional(),  first_only_prompt: z.string(),  default_prompt: z.string().optional(),  max_iteration: z.number(),  memory_config: z.record(z.any()).optional(),  memory_settings: z.record(z.any()).optional(),  tools: z.array(z.any()).optional()});

export const Person_jobNodeSchema = z.object({
  type: z.literal('person_job'),
  data: Person_jobNodeDataSchema,
});