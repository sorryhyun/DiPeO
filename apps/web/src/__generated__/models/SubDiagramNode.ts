// Auto-generated TypeScript model for sub_diagram node
import { z } from 'zod';

export interface SubDiagramNodeData {
  diagram_name?: string | undefined;
}

// Zod schema for validation
export const SubDiagramNodeDataSchema = z.object({
  diagram_name: z.string().optional().describe("Name of the diagram to execute (e.g., 'workflow/process')"),
});
