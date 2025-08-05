
import { BaseNodeData } from './base.js';

export interface UserResponseNodeData extends BaseNodeData {
  prompt: string;
  timeout: number;
}