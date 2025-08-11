
import { BaseNodeData } from './base.js';
import { JsonDict } from '../types/json.js';

export interface JsonSchemaValidatorNodeData extends BaseNodeData {
  schema_path?: string;
  json_schema?: JsonDict;
  data_path?: string;
  strict_mode?: boolean;
  error_on_extra?: boolean;
}