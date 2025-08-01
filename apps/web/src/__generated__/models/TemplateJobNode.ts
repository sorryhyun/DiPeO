







// Auto-generated TypeScript model for template_job node
import { z } from 'zod';

export interface TemplateJobNodeData {
  template_path?: string;
  template_content?: string;
  output_path?: string;
  variables?: Record<string, any>;
  engine?: 'internal' | 'jinja2' | 'handlebars';
}

// Zod schema for validation
export const TemplateJobNodeDataSchema = z.object({
  template_path: z.string().optional(),
  template_content: z.string().optional(),
  output_path: z.string().optional(),
  variables: z.record(z.any()).optional(),
  engine: z.any().optional(),
});