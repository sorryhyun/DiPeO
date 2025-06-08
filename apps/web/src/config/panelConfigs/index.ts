import { startPanelConfig } from './start';
import { conditionPanelConfig } from './condition';
import { jobPanelConfig } from './job';
import { endpointPanelConfig } from './endpoint';
import { personJobPanelConfig } from './personJob';
import { personBatchJobPanelConfig } from './personBatchJob';
import { dbPanelConfig } from './db';
import { userResponsePanelConfig } from './userResponse';
import { notionPanelConfig } from './notion';
import { arrowPanelConfig } from './arrow';
import { personPanelConfig } from './person';

export const PANEL_CONFIGS = {
  start: startPanelConfig,
  condition: conditionPanelConfig,
  job: jobPanelConfig,
  endpoint: endpointPanelConfig,
  person_job: personJobPanelConfig,
  person_batch_job: personBatchJobPanelConfig,
  db: dbPanelConfig,
  user_response: userResponsePanelConfig,
  notion: notionPanelConfig,
  arrow: arrowPanelConfig,
  person: personPanelConfig
};

export * from './start';
export * from './condition';
export * from './job';
export * from './endpoint';
export * from './personJob';
export * from './personBatchJob';
export * from './db';
export * from './userResponse';
export * from './notion';
export * from './arrow';
export * from './person';