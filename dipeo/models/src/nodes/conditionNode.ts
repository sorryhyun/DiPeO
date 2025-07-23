// Auto-generated TypeScript model for condition node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface ConditionNodeData {
  condition_type: string;
  expression?: string;
  node_indices?: any[];
}

export interface ConditionNode extends BaseNode {
  type: 'condition';
  data: ConditionNodeData;
}

// Zod schema for validation
export const ConditionNodeDataSchema = z.object({
  condition_type: z.string(),  expression: z.string().optional(),  node_indices: z.array(z.any()).optional()});

export const ConditionNodeSchema = z.object({
  type: z.literal('condition'),
  data: ConditionNodeDataSchema,
});