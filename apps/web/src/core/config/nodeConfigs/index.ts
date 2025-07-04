import type { NodeType } from '@dipeo/domain-models';
import type { UnifiedNodeConfig } from '../unifiedConfig';

// Import all unified configs
import { startConfig } from './start';
import { conditionConfig } from './condition';
import { codeJobConfig } from './codeJob';
import { apiJobConfig } from './apiJob';
import { endpointConfig } from './endpoint';
import { personJobConfig } from './personJob';
import { personBatchJobConfig } from './personBatchJob';
import { dbConfig } from './db';
import { userResponseConfig } from './userResponse';
import { notionConfig } from './notion';
import { hookConfig } from './hook';

export const UNIFIED_NODE_CONFIGS: Record<NodeType, UnifiedNodeConfig<Record<string, unknown>>> = {
  start: startConfig,
  condition: conditionConfig,
  job: {
    label: 'Job (Deprecated)',
    icon: '⚙️',
    color: 'gray',
    handles: {},
    fields: [],
    defaults: {}
  }, // Deprecated - use code_job or api_job
  code_job: codeJobConfig,
  api_job: apiJobConfig,
  endpoint: endpointConfig,
  person_job: personJobConfig,
  person_batch_job: personBatchJobConfig,
  db: dbConfig,
  user_response: userResponseConfig,
  notion: notionConfig,
  hook: hookConfig
};

// Export individual configs
export { startConfig } from './start';
export { conditionConfig } from './condition';
export { codeJobConfig } from './codeJob';
export { apiJobConfig } from './apiJob';
export { endpointConfig } from './endpoint';
export { personJobConfig } from './personJob';
export { personBatchJobConfig } from './personBatchJob';
export { dbConfig } from './db';
export { userResponseConfig } from './userResponse';
export { notionConfig } from './notion';
export { hookConfig } from './hook';