
import { BaseNodeData } from './base.js';
import { DiagramFormat } from '../enums/diagram.js';

/**
 * Configuration data for SubDiagram nodes that execute other diagrams
 */
export interface SubDiagramNodeData extends BaseNodeData {
  /** Path to sub-diagram file */
  diagram_name?: string;
  /** Diagram format: light or native (default: light) */
  diagram_format?: DiagramFormat;
  /** Pass all current variables to sub-diagram */
  diagram_data?: Record<string, any>;
  /** Enable batch processing for arrays */
  batch?: boolean;
  /** Array variable name for batch processing */
  batch_input_key?: string;
  /** Execute batch items in parallel */
  batch_parallel?: boolean;
  /** Skip if already running as sub-diagram */
  ignoreIfSub?: boolean;
}