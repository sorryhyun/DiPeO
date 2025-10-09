// Auto-generated TypeScript model for sub_diagram node
import { z } from 'zod';
import { PersonID } from '@dipeo/models';
import { DiagramFormat } from '@dipeo/models';

export interface SubDiagramNodeData {
  diagram_name?: string | undefined;
  diagram_data?: Record<string, any> | undefined;
  input_mapping?: Record<string, any> | undefined;
  output_mapping?: Record<string, any> | undefined;
  timeout?: number | undefined;
  wait_for_completion?: boolean | undefined;
  isolate_conversation?: boolean | undefined;
  ignore_if_sub?: boolean | undefined;
  diagram_format?: DiagramFormat | undefined;
  batch?: boolean | undefined;
  batch_input_key?: string | undefined;
  batch_parallel?: boolean | undefined;
}

// Zod schema for validation
export const SubDiagramNodeDataSchema = z.object({
  diagram_name: z.string().optional().describe("Name of the diagram to execute (e.g., 'workflow/process')"),
  diagram_data: z.record(z.any()).optional().describe("Inline diagram data (alternative to diagram_name)"),
  input_mapping: z.record(z.any()).optional().describe("Map node inputs to sub-diagram variables"),
  output_mapping: z.record(z.any()).optional().describe("Map sub-diagram outputs to node outputs"),
  timeout: z.number().min(1).max(3600).optional().describe("Execution timeout in seconds"),
  wait_for_completion: z.boolean().optional().describe("Whether to wait for sub-diagram completion"),
  isolate_conversation: z.boolean().optional().describe("Create isolated conversation context for sub-diagram"),
  ignore_if_sub: z.boolean().optional().describe("Skip execution if this diagram is being run as a sub-diagram"),
  diagram_format: z.any().optional().describe("Format of the diagram file (yaml, json, or light)"),
  batch: z.boolean().optional().describe("Execute sub-diagram in batch mode for multiple inputs"),
  batch_input_key: z.string().optional().describe("Key in inputs containing the array of items for batch processing"),
  batch_parallel: z.boolean().optional().describe("Execute batch items in parallel"),
});
