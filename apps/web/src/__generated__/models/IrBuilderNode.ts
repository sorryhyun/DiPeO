// Auto-generated TypeScript model for ir_builder node
import { z } from 'zod';

export interface IrBuilderNodeData {
  builder_type: enum;
  source_type?: enum | undefined;
  config_path?: string | undefined;
  output_format?: enum | undefined;
  cache_enabled?: boolean | undefined;
  validate_output?: boolean | undefined;
}

// Zod schema for validation
export const IrBuilderNodeDataSchema = z.object({
  builder_type: z.any().describe("Type of IR builder to use"),
  source_type: z.any().optional().describe("Type of source data"),
  config_path: z.string().optional().describe("Path to configuration directory"),
  output_format: z.any().optional().describe("Output format for IR"),
  cache_enabled: z.boolean().optional().describe("Enable IR caching"),
  validate_output: z.boolean().optional().describe("Validate IR structure before output"),
});
