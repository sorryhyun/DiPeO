
import { BaseNodeData } from '../diagram';
import { DiagramFormat } from '../enums';

export interface SubDiagramNodeData extends BaseNodeData {
  diagram_name?: string;
  diagram_format?: DiagramFormat;
  diagram_data?: Record<string, any>;
  batch?: boolean;
  batch_input_key?: string;
  batch_parallel?: boolean;
  ignoreIfSub?: boolean;
}