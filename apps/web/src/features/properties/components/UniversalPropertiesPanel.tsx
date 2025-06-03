import React from 'react';
import { Settings } from 'lucide-react';
import { Panel } from '../wrappers';
import { UNIFIED_NODE_CONFIGS } from '@/shared/types';
import { GenericPropertyPanel } from './ui-components/GenericPropertyPanel';
import {
  endpointConfig,
  personJobConfig,
  conditionConfig,
  dbConfig,
  jobConfig,
  personBatchJobConfig,
  arrowConfig,
  personConfig,
  startConfig
} from '../configs';

// Mapping from node types to their configurations
// Using type assertion as these configs are properly typed individually
const PANEL_CONFIGS = {
  'endpoint': endpointConfig,
  'person_job': personJobConfig,
  'condition': conditionConfig,
  'db': dbConfig,
  'job': jobConfig,
  'person_batch_job': personBatchJobConfig,
  'arrow': arrowConfig,
  'person': personConfig,
  'start': startConfig,
} as const;

export const UniversalPropertiesPanel: React.FC<{ nodeId: string; data: { type: string } }> = ({ nodeId, data }) => {
  const nodeType = data.type;
  const panelConfig = PANEL_CONFIGS[nodeType as keyof typeof PANEL_CONFIGS];
  const nodeConfig = UNIFIED_NODE_CONFIGS[nodeType];
  
  if (!panelConfig) {
    return (
      <Panel icon={<Settings className="w-5 h-5" />} title="Unknown Node Type">
        <div className="text-red-500">No configuration found for node type: {nodeType}</div>
      </Panel>
    );
  }

  return (
    <Panel 
      icon={<span>{nodeConfig?.emoji || '⚙️'}</span>} 
      title={nodeConfig?.propertyTitle || `${nodeType} Properties`}
    >
      <GenericPropertyPanel
        nodeId={nodeId}
        data={data}
        config={panelConfig}
      />
    </Panel>
  );
};