// Auto-generated TypeScript model for condition node
import { z } from 'zod';

export interface ConditionNodeData {
  condition_type: string;
  expression?: string;
  node_indices?: any[];
}

// Zod schema for validation
export const ConditionNodeDataSchema = z.object({
  condition_type: z.string(),
  expression: z.string().optional(),
  node_indices: z.array(z.any()).optional(),
});