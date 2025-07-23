// Auto-generated TypeScript model for sub_diagram node
import { z } from 'zod';
import { BaseNodeData } from '../diagram';

export interface SubDiagramNodeData extends BaseNodeData {
  diagram_name?: string;
  diagram_data?: Record<string, any>;
  input_mapping?: Record<string, any>;
  output_mapping?: Record<string, any>;
  timeout?: number;
  wait_for_completion?: boolean;
  isolate_conversation?: boolean;
}

// Node interface is not needed - will use DomainNode with this data type

// Zod schema for validation
export const SubDiagramNodeDataSchema = z.object({
  diagram_name: z.string().optional(),  diagram_data: z.record(z.any()).optional(),  input_mapping: z.record(z.any()).optional(),  output_mapping: z.record(z.any()).optional(),  timeout: z.number().optional(),  wait_for_completion: z.boolean().optional(),  isolate_conversation: z.boolean().optional()});

// Schema for the node is handled by the main node schema