// Auto-generated TypeScript model for endpoint node
import { z } from 'zod';

export interface EndpointNodeData {
  file_name?: string | undefined;
}

// Zod schema for validation
export const EndpointNodeDataSchema = z.object({
  file_name: z.string().optional().describe("Output filename"),
});
