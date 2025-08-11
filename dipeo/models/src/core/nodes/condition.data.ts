
import { BaseNodeData } from './base.js';
import { ConditionType } from '../enums/node-specific.js';

/**
 * Configuration data for Condition nodes that handle conditional branching
 */
export interface ConditionNodeData extends BaseNodeData {
  /** Condition type: detect_max_iterations, nodes_executed, or custom */
  condition_type?: ConditionType;
  /** Python expression for custom type (access to all variables) */
  expression?: string;
  /** List of node indices for nodes_executed condition type */
  node_indices?: string[];
}