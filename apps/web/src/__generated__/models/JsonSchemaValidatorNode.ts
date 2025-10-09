// Auto-generated TypeScript model for json_schema_validator node
import { z } from 'zod';

export interface JsonSchemaValidatorNodeData {
  json_schema?: Record<string, any> | undefined;
  data_path?: string | undefined;
}

// Zod schema for validation
export const JsonSchemaValidatorNodeDataSchema = z.object({
  json_schema: z.record(z.any()).optional().describe("Inline JSON schema"),
  data_path: z.string().optional().describe("Data Path configuration"),
});
