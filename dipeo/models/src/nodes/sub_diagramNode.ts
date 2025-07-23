// Auto-generated TypeScript model for sub_diagram node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface Sub_diagramNodeData {
  diagram_name?: string;
  diagram_data?: Record<string, any>;
  input_mapping?: Record<string, any>;
  output_mapping?: Record<string, any>;
  timeout?: number;
  wait_for_completion?: boolean;
  isolate_conversation?: boolean;
}

export interface Sub_diagramNode extends BaseNode {
  type: 'sub_diagram';
  data: Sub_diagramNodeData;
}

// Zod schema for validation
export const Sub_diagramNodeDataSchema = z.object({
  diagram_name: z.string().optional(),  diagram_data: z.record(z.any()).optional(),  input_mapping: z.record(z.any()).optional(),  output_mapping: z.record(z.any()).optional(),  timeout: z.number().optional(),  wait_for_completion: z.boolean().optional(),  isolate_conversation: z.boolean().optional()});

export const Sub_diagramNodeSchema = z.object({
  type: z.literal('sub_diagram'),
  data: Sub_diagramNodeDataSchema,
});