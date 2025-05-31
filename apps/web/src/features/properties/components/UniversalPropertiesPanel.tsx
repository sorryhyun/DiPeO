import React from 'react';
import { Settings } from 'lucide-react';
import { Panel } from '../wrappers';
import { UNIFIED_NODE_CONFIGS } from '@/shared/types';
import { PanelConfig } from '@/shared/types/panelConfig';
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
const PANEL_CONFIGS: Record<string, PanelConfig<any>> = {
  'endpoint': endpointConfig,
  'person_job': personJobConfig,
  'condition': conditionConfig,
  'db': dbConfig,
  'job': jobConfig,
  'person_batch_job': personBatchJobConfig,
  'arrow': arrowConfig,
  'person': personConfig,
  'start': startConfig,
};

export const UniversalPropertiesPanel: React.FC<{ nodeId: string; data: any }> = ({ nodeId, data }) => {
  const nodeType = data.type;
  const panelConfig = PANEL_CONFIGS[nodeType];
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