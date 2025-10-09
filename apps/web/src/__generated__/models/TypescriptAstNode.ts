// Auto-generated TypeScript model for typescript_ast node
import { z } from 'zod';
import { PersonID } from '@dipeo/models';

export interface TypescriptAstNodeData {
  source?: string | undefined;
  extract_patterns?: any[] | undefined;
  include_jsdoc?: boolean | undefined;
  parse_mode?: string | undefined;
  transform_enums?: boolean | undefined;
  flatten_output?: boolean | undefined;
  output_format?: string | undefined;
  batch?: boolean | undefined;
  batch_input_key?: string | undefined;
}

// Zod schema for validation
export const TypescriptAstNodeDataSchema = z.object({
  source: z.string().optional().describe("TypeScript source code to parse"),
  extract_patterns: z.any().optional().describe("Patterns to extract from the AST"),
  include_jsdoc: z.boolean().optional().describe("Include JSDoc comments in the extracted data"),
  parse_mode: z.any().optional().describe("TypeScript parsing mode"),
  transform_enums: z.boolean().optional().describe("Transform enum definitions to a simpler format"),
  flatten_output: z.boolean().optional().describe("Flatten the output structure for easier consumption"),
  output_format: z.any().optional().describe("Output format for the parsed data"),
  batch: z.boolean().optional().describe("Enable batch processing mode"),
  batch_input_key: z.string().optional().describe("Key to extract batch items from input"),
});
