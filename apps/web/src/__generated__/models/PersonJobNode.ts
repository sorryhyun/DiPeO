// Auto-generated TypeScript model for person_job node
import { z } from 'zod';

export interface PersonJobNodeData {
  person?: string;
  first_only_prompt: string;
  first_prompt_file?: string;
  default_prompt?: string;
  prompt_file?: string;
  max_iteration: number;
  memorize_to?: string;
  at_most?: number;
  tools?: string;
  text_format?: string;
  text_format_file?: string;
  resolved_prompt?: string;
  resolved_first_prompt?: string;
  batch?: boolean;
  batch_input_key?: string;
  batch_parallel?: boolean;
  max_concurrent?: number;
}

// Zod schema for validation
export const PersonJobNodeDataSchema = z.object({
  person: z.string().optional(),
  first_only_prompt: z.string(),
  first_prompt_file: z.string().optional(),
  default_prompt: z.string().optional(),
  prompt_file: z.string().optional(),
  max_iteration: z.number(),
  memorize_to: z.string().optional(),
  at_most: z.number().min(1).max(500).optional(),
  tools: z.string().optional(),
  text_format: z.string().optional(),
  text_format_file: z.string().optional(),
  resolved_prompt: z.string().optional(),
  resolved_first_prompt: z.string().optional(),
  batch: z.boolean().optional(),
  batch_input_key: z.string().optional(),
  batch_parallel: z.boolean().optional(),
  max_concurrent: z.number().min(1).max(100).optional(),
});
