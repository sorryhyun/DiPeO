// Auto-generated TypeScript model for endpoint node
import { z } from 'zod';
import { PersonID } from '@dipeo/models';

export interface EndpointNodeData {
  save_to_file?: boolean | undefined;
  file_name?: string | undefined;
}

// Zod schema for validation
export const EndpointNodeDataSchema = z.object({
  save_to_file: z.boolean().optional().describe("Save results to file"),
  file_name: z.string().optional().describe("Output filename"),
});
