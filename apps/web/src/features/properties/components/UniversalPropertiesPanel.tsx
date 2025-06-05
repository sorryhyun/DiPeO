import React from 'react';
import { Settings } from 'lucide-react';
import { Panel } from '../wrappers';
import { UNIFIED_NODE_CONFIGS, DiagramNodeData, ArrowData, PersonDefinition } from '@/common/types';
import { PanelConfig } from '@/common/types/panelConfig';
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
  startConfig,
  userResponseConfig
} from '../configs';

// Union type for all possible data types
type UniversalData = DiagramNodeData | (ArrowData & { type: 'arrow' }) | (PersonDefinition & { type: 'person' });

interface UniversalPropertiesPanelProps {
  nodeId: string;
  data: UniversalData;
}

export const UniversalPropertiesPanel: React.FC<UniversalPropertiesPanelProps> = ({ nodeId, data }) => {
  const nodeType = data.type;
  const nodeConfig = UNIFIED_NODE_CONFIGS[nodeType];
  
  // Cast to a more permissive type that accepts the union
  const GenericPanel = GenericPropertyPanel as React.FC<{
    nodeId: string;
    data: Record<string, unknown>;
    config: PanelConfig<Record<string, unknown>>;
  }>;
  
  // Get the appropriate config based on node type
  const getPanelConfig = (): PanelConfig<Record<string, unknown>> | null => {
    switch (nodeType) {
      case 'endpoint':
        return endpointConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'person_job':
        return personJobConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'condition':
        return conditionConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'db':
        return dbConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'job':
        return jobConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'person_batch_job':
        return personBatchJobConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'arrow':
        return arrowConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'person':
        return personConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'start':
        return startConfig as unknown as PanelConfig<Record<string, unknown>>;
      case 'user_response':
        return userResponseConfig as unknown as PanelConfig<Record<string, unknown>>;
      default:
        return null;
    }
  };
  
  const panelConfig = getPanelConfig();
  
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
      <GenericPanel
        nodeId={nodeId}
        data={data as Record<string, unknown>}
        config={panelConfig}
      />
    </Panel>
  );
};