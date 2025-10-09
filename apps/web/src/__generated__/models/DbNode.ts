// Auto-generated TypeScript model for db node
import { z } from 'zod';
import { DBBlockSubType } from '@dipeo/models';

export interface DbNodeData {
  file?: any | undefined;
  collection?: string | undefined;
  sub_type: DBBlockSubType;
  operation: string;
  query?: string | undefined;
  keys?: any | undefined;
  lines?: any | undefined;
  data?: Record<string, any> | undefined;
  serialize_json?: boolean | undefined;
  format?: string | undefined;
}

// Zod schema for validation
export const DbNodeDataSchema = z.object({
  file: z.any().optional().describe("File path or array of file paths"),
  collection: z.string().optional().describe("Database collection name"),
  sub_type: z.any().describe("Database operation type"),
  operation: z.any().describe("Operation configuration"),
  query: z.string().optional().describe("Query configuration"),
  keys: z.any().optional().describe("Single key or list of dot-separated keys to target within the JSON payload"),
  lines: z.any().optional().describe("Line selection or ranges to read (e.g., 1:120 or ['10:20'])"),
  data: z.record(z.any()).optional().describe("Data configuration"),
  serialize_json: z.boolean().optional().describe("Serialize structured data to JSON string (for backward compatibility)"),
  format: z.any().optional().describe("Data format (json, yaml, csv, text, etc.)"),
});
