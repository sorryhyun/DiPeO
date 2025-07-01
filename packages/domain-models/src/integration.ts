/**
 * Integration service domain models
 * These interfaces and enums define external service integrations
 * Separated from core diagram models for better modularity
 */

// LLM Service Providers
export enum LLMService {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  GROK = 'grok',
  BEDROCK = 'bedrock',
  VERTEX = 'vertex',
  DEEPSEEK = 'deepseek'
}

// Notion API Operations
export enum NotionOperation {
  CREATE_PAGE = 'create_page',
  UPDATE_PAGE = 'update_page',
  READ_PAGE = 'read_page',
  DELETE_PAGE = 'delete_page',
  CREATE_DATABASE = 'create_database',
  QUERY_DATABASE = 'query_database',
  UPDATE_DATABASE = 'update_database'
}

import { TokenUsage } from './execution.js';

// LLM Chat Result
export interface ChatResult {
  text: string;
  token_usage?: TokenUsage | null;
  raw_response?: any | null;
}

// Future: Add more integration-related types here
// e.g., SlackOperation, GitHubOperation, etc.