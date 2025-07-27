/**
 * Hook node data interface
 */

import { BaseNodeData } from '../diagram';
import { HookType, HttpMethod } from '../enums';

export interface HookNodeData extends BaseNodeData {
  hook_type: HookType;
  
  // For shell hooks
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  cwd?: string;
  
  // For webhook hooks
  url?: string;
  method?: HttpMethod;
  headers?: Record<string, string>;
  
  // For Python hooks
  script?: string;
  function_name?: string;
  
  // For file hooks  
  file_path?: string;
  format?: 'json' | 'yaml' | 'text';
  
  // Common fields
  timeout?: number;  // in seconds
  retry_count?: number;
  retry_delay?: number;  // in seconds
}