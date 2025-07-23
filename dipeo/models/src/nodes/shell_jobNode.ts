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
  command: z.string(),  args: z.array(z.any()).optional(),  cwd: z.string().optional(),  env: z.record(z.any()).optional(),  timeout: z.number().optional(),  capture_output: z.boolean().optional(),  shell: z.boolean().optional()});

export const Shell_jobNodeSchema = z.object({
  type: z.literal('shell_job'),
  data: Shell_jobNodeDataSchema,
});