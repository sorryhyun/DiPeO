
import { BaseNodeData } from './base.js';
import { DBBlockSubType } from '../enums/node-specific.js';
import { JsonDict } from '../types/json.js';

/**
 * Configuration data for DB nodes that handle file system operations
 */
export interface DBNodeData extends BaseNodeData {
  /** File path(s) - single string or list for multiple files */
  file?: string | string[];
  /** Database collection name (for database operations) */
  collection?: string;
  /** Storage type: file or database */
  sub_type: DBBlockSubType;
  /** Operation type: read or write */
  operation: string;
  /** Database query (for database operations) */
  query?: string;
  /** Data to write (for write operations) */
  data?: JsonDict;
  /** Auto-parse JSON files when reading (default: false) */
  serialize_json?: boolean;
  /** Enable glob pattern expansion for paths (default: false) */
  glob?: boolean;
  /** Data format: json, yaml, csv, text, etc. */
  format?: string;
}