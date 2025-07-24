// Auto-generated TypeScript model for shell_job node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface Shell_jobNodeData {
  command: string;
  args?: any[];
  cwd?: string;
  env?: Record<string, any>;
  timeout?: number;
  capture_output?: boolean;
  shell?: boolean;
}

export interface Shell_jobNode extends BaseNode {
  type: 'shell_job';
  data: Shell_jobNodeData;
}

// Zod schema for validation
export const Shell_jobNodeDataSchema = z.object({
  command: stringSchema,  args: arraySchema.optional(),  cwd: stringSchema.optional(),  env: objectSchema.optional(),  timeout: numberSchema.optional(),  capture_output: booleanSchema.optional(),  shell: booleanSchema.optional()});

export const Shell_jobNodeSchema = z.object({
  type: z.literal('shell_job'),
  data: Shell_jobNodeDataSchema,
});