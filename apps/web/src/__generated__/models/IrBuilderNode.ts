// Auto-generated TypeScript model for ir_builder node
import { z } from 'zod';

export interface IrBuilderNodeData {
  builder_type: 'backend' | 'frontend' | 'strawberry' | 'custom';
  source_type?: 'ast' | 'schema' | 'config' | 'auto';
  config_path?: string;
  output_format?: 'json' | 'yaml' | 'python';
  cache_enabled?: boolean;
  validate_output?: boolean;
}

// Zod schema for validation
export const IrBuilderNodeDataSchema = z.object({
  builder_type: z.enum(["backend", "frontend", "strawberry", "custom"]),
  source_type: z.enum(["ast", "schema", "config", "auto"]).optional(),
  config_path: z.string().optional(),
  output_format: z.enum(["json", "yaml", "python"]).optional(),
  cache_enabled: z.boolean().optional(),
  validate_output: z.boolean().optional(),
});
