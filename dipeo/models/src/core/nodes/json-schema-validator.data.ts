
import { BaseNodeData } from './base.js';

export interface JsonSchemaValidatorNodeData extends BaseNodeData {
  schema_path?: string;
  schema?: Record<string, any>;
  data_path?: string;
  strict_mode?: boolean;
  error_on_extra?: boolean;
}