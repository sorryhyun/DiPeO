// Auto-generated TypeScript model for condition node
import { z } from 'zod';

export interface ConditionNodeData {
  condition_type?: string | undefined;
  expression?: string | undefined;
  person?: PersonID | undefined;
  judge_by?: string | undefined;
  judge_by_file?: string | undefined;
  memorize_to?: string | undefined;
  at_most?: number | undefined;
  expose_index_as?: string | undefined;
}

// Zod schema for validation
export const ConditionNodeDataSchema = z.object({
  condition_type: z.any().optional().describe("Type of condition to evaluate"),
  expression: z.string().optional().describe("Boolean expression to evaluate"),
  person: z.any().optional().describe("AI agent to use for decision making"),
  judge_by: z.string().optional().describe("Prompt for LLM to make a judgment"),
  judge_by_file: z.string().optional().describe("External prompt file path"),
  memorize_to: z.string().optional().describe("Memory control strategy (e.g., GOLDFISH for fresh evaluation)"),
  at_most: z.number().optional().describe("Maximum messages to keep in memory"),
  expose_index_as: z.string().optional().describe("Variable name to expose the condition node's execution count (0-based index) to downstream nodes"),
});
