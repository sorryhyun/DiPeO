
import { BaseNodeData } from './base.js';
import { ConditionType } from '../enums/node-specific.js';

export interface ConditionNodeData extends BaseNodeData {
  condition_type?: ConditionType;
  expression?: string;
  node_indices?: string[];
}