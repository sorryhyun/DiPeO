







// Auto-generated TypeScript model for person_job node
import { z } from 'zod';

export interface PersonJobNodeData {
  person?: string;
  first_only_prompt: string;
  default_prompt?: string;
  max_iteration: number;
  memory_profile?: string;
  memory_config?: Record<string, any>;
  memory_settings?: Record<string, any>;
  tools?: string;
}

// Zod schema for validation
export const PersonJobNodeDataSchema = z.object({
  person: z.string().optional(),
  first_only_prompt: z.string(),
  default_prompt: z.string().optional(),
  max_iteration: z.number(),
  memory_profile: z.string().optional(),
  memory_config: z.record(z.any()).optional(),
  memory_settings: z.record(z.any()).optional(),
  tools: z.string().optional(),
});