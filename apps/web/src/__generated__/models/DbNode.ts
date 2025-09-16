// Auto-generated TypeScript model for db node
import { z } from 'zod';

export interface DbNodeData {
  file?: any | undefined;
  collection?: string | undefined;
  sub_type: enum;
  operation: string;
  query?: string | undefined;
  data?: Record<string, any> | undefined;
  serialize_json?: boolean | undefined;
  format?: string | undefined;
}

// Zod schema for validation
export const DbNodeDataSchema = z.object({
  file: z.any().optional().describe("File path or array of file paths"),
  collection: z.string().optional().describe("Database collection name"),
  sub_type: z.any().describe("Database operation type"),
  operation: z.string().describe("Operation configuration"),
  query: z.string().optional().describe("Query configuration"),
  data: z.record(z.any()).optional().describe("Data configuration"),
  serialize_json: z.boolean().optional().describe("Serialize structured data to JSON string (for backward compatibility)"),
  format: z.string().optional().describe("Data format (json, yaml, csv, text, etc.)"),
});
