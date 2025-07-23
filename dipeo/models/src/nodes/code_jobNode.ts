// Auto-generated TypeScript model for code_job node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface Code_jobNodeData {
  language: any;
  filePath: string;
  functionName?: string;
  timeout?: number;
}

export interface Code_jobNode extends BaseNode {
  type: 'code_job';
  data: Code_jobNodeData;
}

// Zod schema for validation
export const Code_jobNodeDataSchema = z.object({
  language: z.any(),  filePath: z.string(),  functionName: z.string().optional(),  timeout: z.number().optional()});

export const Code_jobNodeSchema = z.object({
  type: z.literal('code_job'),
  data: Code_jobNodeDataSchema,
});