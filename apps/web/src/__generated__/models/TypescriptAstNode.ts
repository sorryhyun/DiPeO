// Auto-generated TypeScript model for typescript_ast node
import { z } from 'zod';

export interface TypescriptAstNodeData {
  source?: string | undefined;
  extract_patterns?: any[] | undefined;
  parse_mode?: string | undefined;
  output_format?: string | undefined;
  batch_input_key?: string | undefined;
}

// Zod schema for validation
export const TypescriptAstNodeDataSchema = z.object({
  source: z.string().optional().describe("TypeScript source code to parse"),
  extract_patterns: z.any().optional().describe("Patterns to extract from the AST"),
  parse_mode: z.any().optional().describe("TypeScript parsing mode"),
  output_format: z.any().optional().describe("Output format for the parsed data"),
  batch_input_key: z.string().optional().describe("Key to extract batch items from input"),
});
