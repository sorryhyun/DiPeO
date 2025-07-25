// Auto-generated TypeScript model for db node
import { z } from 'zod';


export interface DbNodeData {

  file?: string;

  collection?: string;

  sub_type: 'fixed_prompt' | 'file' | 'code' | 'api_tool';

  operation: string;

  query?: string;

  data?: Record<string, any>;

}

// Zod schema for validation
export const DbNodeDataSchema = z.object({

  file: z.string().optional(),

  collection: z.string().optional(),

  sub_type: z.enum(["fixed_prompt", "file", "code", "api_tool"]),

  operation: z.string(),

  query: z.string().optional(),

  data: z.record(z.any()).optional(),

});