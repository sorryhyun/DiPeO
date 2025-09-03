
import { BaseNodeData } from './base.js';
import { ConditionType } from '../enums/node-specific.js';
import { PersonID } from '../diagram.js';

/**
 * Configuration data for Condition nodes that handle conditional branching
 */
export interface ConditionNodeData extends BaseNodeData {
  /** Condition type: detect_max_iterations, nodes_executed, custom, or llm_decision */
  condition_type?: ConditionType;
  /** Python expression for custom type (access to all variables) */
  expression?: string;
  /** List of node indices for nodes_executed condition type */
  node_indices?: string[];
  /** Variable name to expose the condition node's execution count (0-based index) to downstream nodes */
  expose_index_as?: string;
  /** When true, downstream nodes can execute even if this condition hasn't been evaluated yet */
  skippable?: boolean;
  
  // LLM_DECISION specific fields
  /** AI agent to use (when condition_type is LLM_DECISION) */
  person?: PersonID;
  /** The prompt/criteria for LLM to judge */
  judge_by?: string;
  /** External prompt file in {subdirectory}/prompts/ */
  judge_by_file?: string;
  /** Memory control (e.g., "GOLDFISH" for fresh evaluation) */
  memorize_to?: string;
  /** Max messages to keep in memory */
  at_most?: number;
}