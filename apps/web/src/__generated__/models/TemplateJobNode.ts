// Auto-generated TypeScript model for template_job node
import { z } from 'zod';

export interface TemplateJobNodeData {
  template_content?: string | undefined;
  variables?: Record<string, any> | undefined;
  engine?: string | undefined;
  preprocessor?: string | undefined;
}

// Zod schema for validation
export const TemplateJobNodeDataSchema = z.object({
  template_content: z.string().optional().describe("Inline template content"),
  variables: z.record(z.any()).optional().describe("Variables configuration"),
  engine: z.any().optional().describe("Template engine to use"),
  preprocessor: z.string().optional().describe("Preprocessor function to apply before templating"),
});
