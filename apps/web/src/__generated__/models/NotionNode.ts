







// Auto-generated TypeScript model for notion node
import { z } from 'zod';

export interface NotionNodeData {
  api_key: string;
  database_id: string;
  operation: string;
  page_id?: string;
}

// Zod schema for validation
export const NotionNodeDataSchema = z.object({
  api_key: z.string(),
  database_id: z.string(),
  operation: z.string(),
  page_id: z.string().optional(),
});