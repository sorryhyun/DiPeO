// Auto-generated TypeScript model for json_schema_validator node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface Json_schema_validatorNodeData {
  schema_path?: string;
  schema?: Record<string, any>;
  data_path?: string;
  strict_mode?: boolean;
  error_on_extra?: boolean;
}

export interface Json_schema_validatorNode extends BaseNode {
  type: 'json_schema_validator';
  data: Json_schema_validatorNodeData;
}

// Zod schema for validation
export const Json_schema_validatorNodeDataSchema = z.object({
  schema_path: z.string().optional(),  schema: z.record(z.any()).optional(),  data_path: z.string().optional(),  strict_mode: z.boolean().optional(),  error_on_extra: z.boolean().optional()});

export const Json_schema_validatorNodeSchema = z.object({
  type: z.literal('json_schema_validator'),
  data: Json_schema_validatorNodeDataSchema,
});