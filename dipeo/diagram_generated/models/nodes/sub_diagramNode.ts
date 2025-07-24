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
  diagram_name: stringSchema.optional(),  diagram_data: objectSchema.optional(),  input_mapping: objectSchema.optional(),  output_mapping: objectSchema.optional(),  timeout: numberSchema.optional(),  wait_for_completion: booleanSchema.optional(),  isolate_conversation: booleanSchema.optional()});

export const Sub_diagramNodeSchema = z.object({
  type: z.literal('sub_diagram'),
  data: Sub_diagramNodeDataSchema,
});