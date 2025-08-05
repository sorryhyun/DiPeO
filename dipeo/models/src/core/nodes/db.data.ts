
import { BaseNodeData } from './base.js';
import { DBBlockSubType } from '../enums/node-specific.js';

export interface DBNodeData extends BaseNodeData {
  file?: string | string[];
  collection?: string;
  sub_type: DBBlockSubType;
  operation: string;
  query?: string;
  data?: Record<string, any>;
  serialize_json?: boolean;
  glob?: boolean;  // Enable glob pattern expansion for file paths
}