// Generated from specification: sub_diagram
import { BaseNodeData } from './BaseNode';

export interface SubDiagramNodeData extends BaseNodeData {
  diagram_name?: string;
  diagram_data?: Record&lt;string, any&gt;;
  input_mapping?: Record&lt;string, any&gt;;
  output_mapping?: Record&lt;string, any&gt;;
  timeout?: number;
  wait_for_completion?: boolean;
  isolate_conversation?: boolean;
}