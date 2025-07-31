
import { BaseNodeData } from '../diagram';

export interface ConditionNodeData extends BaseNodeData {
  condition_type: string;
  expression?: string;
  node_indices?: string[];
}