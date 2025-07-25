// Auto-generated TypeScript model for json_schema_validator node
import { z } from 'zod';


export interface JsonSchemaValidatorNodeData {

  schema_path?: string;

  schema?: Record<string, any>;

  data_path?: string;

  strict_mode?: boolean;

  error_on_extra?: boolean;

}

// Zod schema for validation
export const JsonSchemaValidatorNodeDataSchema = z.object({

  schema_path: z.string().optional(),

  schema: z.record(z.any()).optional(),

  data_path: z.string().optional(),

  strict_mode: z.boolean().optional(),

  error_on_extra: z.boolean().optional(),

});