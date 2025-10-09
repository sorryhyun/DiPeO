// Auto-generated TypeScript model for ir_builder node
import { z } from 'zod';

export interface IrBuilderNodeData {
  builder_type: string;
  source_type?: string | undefined;
  config_path?: string | undefined;
  output_format?: string | undefined;
}

// Zod schema for validation
export const IrBuilderNodeDataSchema = z.object({
  builder_type: z.any().describe("Type of IR builder to use"),
  source_type: z.any().optional().describe("Type of source data"),
  config_path: z.string().optional().describe("Path to configuration directory"),
  output_format: z.any().optional().describe("Output format for IR"),
});
