// Auto-generated TypeScript model for typescript_ast node
import { z } from 'zod';

export interface TypescriptAstNodeData {
  source: string;
  extractPatterns?: any[] | undefined;
  includeJSDoc?: boolean | undefined;
  parseMode?: string | undefined;
  transformEnums?: boolean | undefined;
  flattenOutput?: boolean | undefined;
  outputFormat?: string | undefined;
  batch?: boolean | undefined;
  batchInputKey?: string | undefined;
}

// Zod schema for validation
export const TypescriptAstNodeDataSchema = z.object({
  source: z.string().describe("TypeScript source code to parse"),
  extractPatterns: z.any().optional().describe("Patterns to extract from the AST"),
  includeJSDoc: z.boolean().optional().describe("Include JSDoc comments in the extracted data"),
  parseMode: z.any().optional().describe("TypeScript parsing mode"),
  transformEnums: z.boolean().optional().describe("Transform enum definitions to a simpler format"),
  flattenOutput: z.boolean().optional().describe("Flatten the output structure for easier consumption"),
  outputFormat: z.any().optional().describe("Output format for the parsed data"),
  batch: z.boolean().optional().describe("Enable batch processing mode"),
  batchInputKey: z.string().optional().describe("Key to extract batch items from input"),
});
