// Auto-generated TypeScript model for condition node
import { z } from 'zod';

export interface ConditionNodeData {
  condition_type?: 'detect_max_iterations' | 'check_nodes_executed' | 'custom';
  expression?: string;
  node_indices?: any[];
}

// Zod schema for validation
export const ConditionNodeDataSchema = z.object({
  condition_type: z.enum(["detect_max_iterations", "check_nodes_executed", "custom"]).optional(),
  expression: z.string().optional(),
  node_indices: z.array(z.any()).optional(),
});