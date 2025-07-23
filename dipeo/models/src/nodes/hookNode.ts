// Generated from specification: hook
import { BaseNodeData } from '../diagram';

export interface HookNodeData extends BaseNodeData {
  hook_type: 'shell' | 'http' | 'python' | 'file';
  command?: string;
  url?: string;
  timeout?: number;
  retry_count?: number;
}