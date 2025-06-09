/**
 * Unified node configurations that combine both node and panel configs
 */

import type { NodeKind } from '@/types';
import type { UnifiedNodeConfig } from '../unifiedConfig';

// Import all unified configs
import { startUnifiedConfig } from './startUnified';
import { conditionUnifiedConfig } from './conditionUnified';
import { jobUnifiedConfig } from './jobUnified';
import { endpointUnifiedConfig } from './endpointUnified';
import { personJobUnifiedConfig } from './personJobUnified';
import { personBatchJobUnifiedConfig } from './personBatchJobUnified';
import { dbUnifiedConfig } from './dbUnified';
import { userResponseUnifiedConfig } from './userResponseUnified';
import { notionUnifiedConfig } from './notionUnified';

export const UNIFIED_NODE_CONFIGS: Record<NodeKind, UnifiedNodeConfig<any>> = {
  start: startUnifiedConfig,
  condition: conditionUnifiedConfig,
  job: jobUnifiedConfig,
  endpoint: endpointUnifiedConfig,
  person_job: personJobUnifiedConfig,
  person_batch_job: personBatchJobUnifiedConfig,
  db: dbUnifiedConfig,
  user_response: userResponseUnifiedConfig,
  notion: notionUnifiedConfig
};

// Export individual configs
export { startUnifiedConfig } from './startUnified';
export { conditionUnifiedConfig } from './conditionUnified';
export { jobUnifiedConfig } from './jobUnified';
export { endpointUnifiedConfig } from './endpointUnified';
export { personJobUnifiedConfig } from './personJobUnified';
export { personBatchJobUnifiedConfig } from './personBatchJobUnified';
export { dbUnifiedConfig } from './dbUnified';
export { userResponseUnifiedConfig } from './userResponseUnified';
export { notionUnifiedConfig } from './notionUnified';