// Auto-generated TypeScript model for endpoint node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface EndpointNodeData {
  save_to_file: boolean;
  file_name?: string;
}

export interface EndpointNode extends BaseNode {
  type: 'endpoint';
  data: EndpointNodeData;
}

// Zod schema for validation
export const EndpointNodeDataSchema = z.object({
  save_to_file: booleanSchema,  file_name: stringSchema.optional()});

export const EndpointNodeSchema = z.object({
  type: z.literal('endpoint'),
  data: EndpointNodeDataSchema,
});