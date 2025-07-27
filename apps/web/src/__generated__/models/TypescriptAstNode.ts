// Auto-generated TypeScript model for typescript_ast node
import { z } from 'zod';

export interface TypescriptAstNodeData {
  source: string;
  extractPatterns?: any[];
  includeJSDoc?: boolean;
  parseMode?: string;
  transformEnums?: boolean;
  flattenOutput?: boolean;
  outputFormat?: string;
}

// Zod schema for validation
export const TypescriptAstNodeDataSchema = z.object({
  source: z.string(),
  extractPatterns: z.array(z.any()).optional(),
  includeJSDoc: z.boolean().optional(),
  parseMode: z.any().optional(),
  transformEnums: z.boolean().optional(),
  flattenOutput: z.boolean().optional(),
  outputFormat: z.any().optional(),
});