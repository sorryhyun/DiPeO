/**
 * Start node data interface
 */

import { BaseNodeData } from '../diagram';
import { HookTriggerMode } from '../enums';

export interface StartNodeData extends BaseNodeData {
  custom_data: Record<string, string | number | boolean>;
  output_data_structure: Record<string, string>;
  trigger_mode?: HookTriggerMode;
  hook_event?: string;  // Event name to listen for when trigger_mode is 'hook'
  hook_filters?: Record<string, any>;  // Filters to match specific events
}