/**
 * Start node data interface
 */

import { BaseNodeData } from '../diagram';
import { HookTriggerMode } from '../enums';

export interface StartNodeData extends BaseNodeData {
  trigger_mode: HookTriggerMode;  // Required field with default 'none'
  custom_data?: Record<string, string | number | boolean>;  // Only for manual trigger
  output_data_structure?: Record<string, string>;  // Only for manual trigger
  hook_event?: string;  // Event name to listen for when trigger_mode is 'hook'
  hook_filters?: Record<string, any>;  // Filters to match specific events
}