
import { BaseNodeData } from '../diagram';
import { HookType, HttpMethod } from '../enums';

export interface HookNodeData extends BaseNodeData {
  hook_type: HookType;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  cwd?: string;
  url?: string;
  method?: HttpMethod;
  headers?: Record<string, string>;
  script?: string;
  function_name?: string;
  file_path?: string;
  format?: 'json' | 'yaml' | 'text';
  timeout?: number;
  retry_count?: number;
  retry_delay?: number;
}