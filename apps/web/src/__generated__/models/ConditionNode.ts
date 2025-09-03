// Auto-generated TypeScript model for condition node
import { z } from 'zod';

export interface ConditionNodeData {
  condition_type?: 'detect_max_iterations' | 'check_nodes_executed' | 'custom' | 'llm_decision';
  expression?: string;
  node_indices?: any[];
  person?: string;
  judge_by?: string;
  judge_by_file?: string;
  memorize_to?: string;
  at_most?: number;
  expose_index_as?: string;
  skippable?: boolean;
}

// Zod schema for validation
export const ConditionNodeDataSchema = z.object({
  condition_type: z.enum(["detect_max_iterations", "check_nodes_executed", "custom", "llm_decision"]).optional(),
  expression: z.string().optional(),
  node_indices: z.array(z.any()).optional(),
  person: z.string().optional(),
  judge_by: z.string().optional(),
  judge_by_file: z.string().optional(),
  memorize_to: z.string().optional(),
  at_most: z.number().optional(),
  expose_index_as: z.string().optional(),
  skippable: z.boolean().optional(),
});