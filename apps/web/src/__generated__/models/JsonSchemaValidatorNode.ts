// Auto-generated TypeScript model for json_schema_validator node
import { z } from 'zod';

export interface JsonSchemaValidatorNodeData {
  schema_path?: string | undefined;
  schema?: Record<string, any> | undefined;
  data_path?: string | undefined;
  strict_mode?: boolean | undefined;
  error_on_extra?: boolean | undefined;
}

// Zod schema for validation
export const JsonSchemaValidatorNodeDataSchema = z.object({
  schema_path: z.string().optional().describe("Path to JSON schema file"),
  schema: z.record(z.any()).optional().describe("Inline JSON schema"),
  data_path: z.string().optional().describe("Data Path configuration"),
  strict_mode: z.boolean().optional().describe("Strict Mode configuration"),
  error_on_extra: z.boolean().optional().describe("Error On Extra configuration"),
});
