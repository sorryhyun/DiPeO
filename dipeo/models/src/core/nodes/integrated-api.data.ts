/**
 * Integrated API node data interface
 * Supports multiple API providers through a unified interface
 */

import { BaseNodeData } from './base.js';
import { APIServiceType } from '../enums/integrations.js';
import { JsonDict } from '../types/json.js';

export interface IntegratedApiNodeData extends BaseNodeData {
  /**
   * The API provider to use (e.g., notion, slack, github)
   */
  provider: APIServiceType;
  
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
 * Provider-specific operation definitions
 * These will be used for validation and UI generation
 */
export const PROVIDER_OPERATIONS: Record<APIServiceType, string[]> = {
  [APIServiceType.NOTION]: [
    'create_page',
    'update_page',
    'read_page',
    'delete_page',
    'create_database',
    'query_database',
    'update_database'
  ],
  [APIServiceType.SLACK]: [
    'send_message',
    'read_channel',
    'create_channel',
    'list_channels',
    'upload_file'
  ],
  [APIServiceType.GITHUB]: [
    'create_issue',
    'update_issue',
    'list_issues',
    'create_pr',
    'merge_pr',
    'get_repo_info'
  ],
  [APIServiceType.JIRA]: [
    'create_issue',
    'update_issue',
    'search_issues',
    'transition_issue',
    'add_comment'
  ],
  // LLM providers shouldn't be used with this node
  [APIServiceType.OPENAI]: [],
  [APIServiceType.ANTHROPIC]: [],
  [APIServiceType.GOOGLE]: [],
  [APIServiceType.GEMINI]: [],
  [APIServiceType.BEDROCK]: [],
  [APIServiceType.VERTEX]: [],
  [APIServiceType.DEEPSEEK]: [],
  [APIServiceType.OLLAMA]: [],
  [APIServiceType.GOOGLE_SEARCH]: [
    'search'
  ]
};