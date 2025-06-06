import React from 'react';
import { Settings } from 'lucide-react';
import { DiagramNodeData, ArrowData, PersonDefinition } from '../../../types';
import { NODE_CONFIGS } from '../../../config/nodes';
import { PanelConfig } from '../../../types';
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
  userResponseConfig,
  notionConfig
} from '../configs';

// Union type for all possible data types
type UniversalData = DiagramNodeData | (ArrowData & { type: 'arrow' }) | (PersonDefinition & { type: 'person' });

interface UniversalPropertiesPanelProps {
  nodeId: string;
  data: UniversalData;
}

export const UniversalPropertiesPanel: React.FC<UniversalPropertiesPanelProps> = ({ nodeId, data }) => {
  const nodeType = data.type;
  const nodeConfig = nodeType in NODE_CONFIGS ? NODE_CONFIGS[nodeType as keyof typeof NODE_CONFIGS] : undefined;
  
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
      case 'notion':
        return notionConfig as unknown as PanelConfig<Record<string, unknown>>;
      default:
        return null;
    }
  };
  
  const panelConfig = getPanelConfig();
  
  if (!panelConfig) {
    return (
      <div className="p-4 space-y-4">
        <div className="flex items-center space-x-2 border-b pb-2">
          <Settings className="w-5 h-5" />
          <h3 className="text-lg font-semibold">Unknown Node Type</h3>
        </div>
        <div className="space-y-4">
          <div className="text-red-500">No configuration found for node type: {nodeType}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center space-x-2 border-b pb-2">
        <span>{nodeConfig?.icon || '⚙️'}</span>
        <h3 className="text-lg font-semibold">
          {nodeConfig?.label ? `${nodeConfig.label} Properties` : `${nodeType} Properties`}
        </h3>
      </div>
      <div className="space-y-4">
        <GenericPanel
          nodeId={nodeId}
          data={data as Record<string, unknown>}
          config={panelConfig}
        />
      </div>
    </div>
  );
};