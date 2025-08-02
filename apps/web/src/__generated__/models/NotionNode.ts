







// Auto-generated TypeScript model for notion node
import { z } from 'zod';

export interface NotionNodeData {
  api_key: string;
  database_id: string;
  operation: 'query_database' | 'create_page' | 'update_page' | 'read_page' | 'delete_page' | 'create_database' | 'update_database';
  page_id?: string;
}

// Zod schema for validation
export const NotionNodeDataSchema = z.object({
  api_key: z.string(),
  database_id: z.string(),
  operation: z.any(),
  page_id: z.string().optional(),
});