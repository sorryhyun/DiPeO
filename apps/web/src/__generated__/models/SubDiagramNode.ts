// Auto-generated TypeScript model for sub_diagram node
import { z } from 'zod';
import { DiagramFormat } from '@dipeo/models';

export interface SubDiagramNodeData {
  diagram_name?: string | undefined;
  diagram_data?: Record<string, any> | undefined;
  input_mapping?: Record<string, any> | undefined;
  output_mapping?: Record<string, any> | undefined;
  timeout?: number | undefined;
  diagram_format?: DiagramFormat | undefined;
  batch_input_key?: string | undefined;
}

// Zod schema for validation
export const SubDiagramNodeDataSchema = z.object({
  diagram_name: z.string().optional().describe("Name of the diagram to execute (e.g., 'workflow/process')"),
  diagram_data: z.record(z.any()).optional().describe("Inline diagram data (alternative to diagram_name)"),
  input_mapping: z.record(z.any()).optional().describe("Map node inputs to sub-diagram variables"),
  output_mapping: z.record(z.any()).optional().describe("Map sub-diagram outputs to node outputs"),
  timeout: z.number().min(1).max(3600).optional().describe("Execution timeout in seconds"),
  diagram_format: z.any().optional().describe("Format of the diagram file (yaml, json, or light)"),
  batch_input_key: z.string().optional().describe("Key in inputs containing the array of items for batch processing"),
});
