







// Auto-generated TypeScript model for sub_diagram node
import { z } from 'zod';

export interface SubDiagramNodeData {
  diagram_name?: string;
  diagram_data?: Record<string, any>;
  input_mapping?: Record<string, any>;
  output_mapping?: Record<string, any>;
  timeout?: number;
  wait_for_completion?: boolean;
  isolate_conversation?: boolean;
  ignoreIfSub?: boolean;
  diagram_format?: 'yaml' | 'json' | 'light';
  batch?: boolean;
  batch_input_key?: string;
  batch_parallel?: boolean;
}

// Zod schema for validation
export const SubDiagramNodeDataSchema = z.object({
  diagram_name: z.string().optional(),
  diagram_data: z.record(z.any()).optional(),
  input_mapping: z.record(z.any()).optional(),
  output_mapping: z.record(z.any()).optional(),
  timeout: z.number().min(1).max(3600).optional(),
  wait_for_completion: z.boolean().optional(),
  isolate_conversation: z.boolean().optional(),
  ignoreIfSub: z.boolean().optional(),
  diagram_format: z.any().optional(),
  batch: z.boolean().optional(),
  batch_input_key: z.string().optional(),
  batch_parallel: z.boolean().optional(),
});