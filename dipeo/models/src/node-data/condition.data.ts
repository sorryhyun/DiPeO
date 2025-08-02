
import { BaseNodeData } from '../diagram';
import { ConditionType } from '../enums';

export interface ConditionNodeData extends BaseNodeData {
  condition_type?: ConditionType;
  expression?: string;
  node_indices?: string[];
}