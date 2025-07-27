/**
 * JSON schema validator node data interface
 */

import { BaseNodeData } from '../diagram';

export interface JsonSchemaValidatorNodeData extends BaseNodeData {
  schema_path?: string;  // Path to JSON schema file
  schema?: Record<string, any>;  // Inline schema definition
  data_path?: string;  // Path to data file to validate
  strict_mode?: boolean;  // Whether to use strict validation
  error_on_extra?: boolean;  // Error on extra properties
}