/**
 * Integrated API node data interface
 * Supports multiple API providers through a unified interface
 */

import { BaseNodeData } from './base.js';
import { JsonDict } from '../types/json.js';

export interface IntegratedApiNodeData extends BaseNodeData {
  /**
   * Provider id from the dynamic registry (e.g., 'notion', 'slack')
   */
  provider: string;
  
  /**
   * The operation to perform (provider-specific)
   * This is a string to allow dynamic operations per provider
   */
  operation: string;
  
  /**
   * Provider-specific configuration
   * Structure depends on the selected provider and operation
   */
  config?: JsonDict;
  
  /**
   * Optional resource ID (e.g., page_id for Notion, channel_id for Slack)
   */
  resource_id?: string;
  
  /**
   * Request timeout in seconds
   */
  timeout?: number;
  
  /**
   * Maximum number of retries for failed requests
   */
  max_retries?: number;
}

/**
 * @deprecated Provider operations are now dynamically loaded from the provider registry
 * This static definition is kept only for backward compatibility during transition
 */
export const PROVIDER_OPERATIONS: Record<string, string[]> = {
  'notion': [
    'create_page',
    'update_page',
    'read_page',
    'delete_page',
    'create_database',
    'query_database',
    'update_database'
  ],
  'slack': [
    'send_message',
    'read_channel',
    'create_channel',
    'list_channels',
    'upload_file'
  ],
  'github': [
    'create_issue',
    'update_issue',
    'list_issues',
    'create_pr',
    'merge_pr',
    'get_repo_info'
  ],
  'jira': [
    'create_issue',
    'update_issue',
    'search_issues',
    'transition_issue',
    'add_comment'
  ],
  'google_search': [
    'search'
  ]
};