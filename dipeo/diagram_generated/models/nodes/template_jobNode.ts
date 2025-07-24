// Auto-generated TypeScript model for template_job node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface Template_jobNodeData {
  template_path?: string;
  template_content?: string;
  output_path?: string;
  variables?: Record<string, any>;
  engine?: any;
}

export interface Template_jobNode extends BaseNode {
  type: 'template_job';
  data: Template_jobNodeData;
}

// Zod schema for validation
export const Template_jobNodeDataSchema = z.object({
  template_path: stringSchema.optional(),  template_content: stringSchema.optional(),  output_path: stringSchema.optional(),  variables: objectSchema.optional(),  engine: enumSchema.optional()});

export const Template_jobNodeSchema = z.object({
  type: z.literal('template_job'),
  data: Template_jobNodeDataSchema,
});