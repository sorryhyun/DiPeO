// Auto-generated TypeScript model for typescript_ast node
import { z } from 'zod';

export interface TypescriptAstNodeData {
  extract_patterns?: any[] | undefined;
}

// Zod schema for validation
export const TypescriptAstNodeDataSchema = z.object({
  extract_patterns: z.any().optional().describe("Patterns to extract from the AST"),
});
