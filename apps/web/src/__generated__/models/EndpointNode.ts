// Auto-generated TypeScript model for endpoint node
import { z } from 'zod';

export interface EndpointNodeData {
  save_to_file: boolean;
  file_name?: string;
}

// Zod schema for validation
export const EndpointNodeDataSchema = z.object({
  save_to_file: z.boolean(),
  file_name: z.string().optional(),
});
