// Auto-generated TypeScript model for typescript_ast node
import { z } from 'zod';

export interface TypescriptAstNodeData {
  source: string;
  extractPatterns?: any[];
  includeJSDoc?: boolean;
  parseMode?: string;
}

// Zod schema for validation
export const TypescriptAstNodeDataSchema = z.object({
  source: z.string(),
  extractPatterns: z.array(z.any()).optional(),
  includeJSDoc: z.boolean().optional(),
  parseMode: z.any().optional(),
});