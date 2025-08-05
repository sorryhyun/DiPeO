







// Auto-generated TypeScript model for person_job node
import { z } from 'zod';

export interface PersonJobNodeData {
  person?: string;
  first_only_prompt: string;
  default_prompt?: string;
  prompt_file?: string;
  max_iteration: number;
  memory_profile?: 'O' | 'b' | 'j' | 'e' | 'c' | 't' | '.' | 'v' | 'a' | 'l' | 'u' | 'e' | 's' | '(' | 'M' | 'e' | 'm' | 'o' | 'r' | 'y' | 'P' | 'r' | 'o' | 'f' | 'i' | 'l' | 'e' | ')';
  tools?: string;
  memory_settings?: Record<string, any>;
}

// Zod schema for validation
export const PersonJobNodeDataSchema = z.object({
  person: z.string().optional(),
  first_only_prompt: z.string(),
  default_prompt: z.string().optional(),
  prompt_file: z.string().optional(),
  max_iteration: z.number(),
  memory_profile: z.any().optional(),
  tools: z.string().optional(),
  memory_settings: z.record(z.any()).optional(),
});