/**
 * Sub-diagram node data interface
 */

import { BaseNodeData } from '../diagram';
import { DiagramFormat } from '../enums';

export interface SubDiagramNodeData extends BaseNodeData {
  diagram_name?: string;  // Name of the diagram to execute (e.g., "workflow/process")
  diagram_format?: DiagramFormat;  // Format of the diagram file (native, light, readable)
  diagram_data?: Record<string, any>;  // Inline diagram data (alternative to diagram_name)
  batch?: boolean;  // Execute sub-diagram for each item in the input array
  batch_input_key?: string;  // Key in inputs containing the array to iterate over (default: "items")
  batch_parallel?: boolean;  // Execute batch items in parallel (default: true)
}