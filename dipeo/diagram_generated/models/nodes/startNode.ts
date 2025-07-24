// Auto-generated TypeScript model for start node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface StartNodeData {
  custom_data: string;
  output_data_structure: Record<string, any>;
  trigger_mode?: any;
  hook_event?: string;
  hook_filters?: Record<string, any>;
}

export interface StartNode extends BaseNode {
  type: 'start';
  data: StartNodeData;
}

// Zod schema for validation
export const StartNodeDataSchema = z.object({
  custom_data: stringSchema,  output_data_structure: objectSchema,  trigger_mode: enumSchema.optional(),  hook_event: stringSchema.optional(),  hook_filters: objectSchema.optional()});

export const StartNodeSchema = z.object({
  type: z.literal('start'),
  data: StartNodeDataSchema,
});