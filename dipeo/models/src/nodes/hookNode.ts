// Auto-generated TypeScript model for hook node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface HookNodeData {
  hook_type: any;
  command?: string;
  url?: string;
  timeout?: number;
  retry_count?: number;
}

export interface HookNode extends BaseNode {
  type: 'hook';
  data: HookNodeData;
}

// Zod schema for validation
export const HookNodeDataSchema = z.object({
  hook_type: z.any(),  command: z.string().optional(),  url: z.string().optional(),  timeout: z.number().optional(),  retry_count: z.number().optional()});

export const HookNodeSchema = z.object({
  type: z.literal('hook'),
  data: HookNodeDataSchema,
});