// Auto-generated TypeScript model for person_batch_job node
import { z } from 'zod';

export interface PersonBatchJobNodeData {
  person?: string;
  batch_key: string;
  prompt: string;
}

// Zod schema for validation
export const PersonBatchJobNodeDataSchema = z.object({
  person: z.string().optional(),
  batch_key: z.string(),
  prompt: z.string(),
});
