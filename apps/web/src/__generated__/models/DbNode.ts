// Auto-generated TypeScript model for db node
import { z } from 'zod';

export interface DbNodeData {
  file?: any | undefined;
  keys?: any | undefined;
  lines?: any | undefined;
}

// Zod schema for validation
export const DbNodeDataSchema = z.object({
  file: z.any().optional().describe("File path or array of file paths"),
  keys: z.any().optional().describe("Single key or list of dot-separated keys to target within the JSON payload"),
  lines: z.any().optional().describe("Line selection or ranges to read (e.g., 1:120 or ['10:20'])"),
});
