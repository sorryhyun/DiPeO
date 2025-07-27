/**
 * User response node data interface
 */

import { BaseNodeData } from '../diagram';

export interface UserResponseNodeData extends BaseNodeData {
  prompt: string;
  timeout: number;
}