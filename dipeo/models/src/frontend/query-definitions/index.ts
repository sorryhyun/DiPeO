/**
 * GraphQL Query Definitions Index
 * Exports all entity query definitions
 */

export * from './types';
export * from './diagrams';
export * from './persons';
export * from './executions';
export * from './api-keys';
export * from './conversations';
export * from './system';
export * from './files';
export * from './nodes';
export * from './formats';
export * from './prompts';
export * from './cli-sessions';

// Re-export as a collection for convenience
import { diagramQueries } from './diagrams';
import { personQueries } from './persons';
import { executionQueries } from './executions';
import { apiKeyQueries } from './api-keys';
import { conversationQueries } from './conversations';
import { systemQueries } from './system';
import { fileQueries } from './files';
import { nodeQueries } from './nodes';
import { formatQueries } from './formats';
import { promptQueries } from './prompts';
import { cliSessionQueries } from './cli-sessions';

export const allQueryDefinitions = [
  diagramQueries,
  personQueries,
  executionQueries,
  apiKeyQueries,
  conversationQueries,
  systemQueries,
  fileQueries,
  nodeQueries,
  formatQueries,
  promptQueries,
  cliSessionQueries
];