// Auto-generated TypeScript model for ir_builder node
import { z } from 'zod';
import { PersonID } from '@dipeo/models';

export interface IrBuilderNodeData {
  builder_type: string;
  source_type?: string | undefined;
  config_path?: string | undefined;
  output_format?: string | undefined;
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
