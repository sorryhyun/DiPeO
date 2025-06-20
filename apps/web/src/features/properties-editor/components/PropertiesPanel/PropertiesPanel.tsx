import React from 'react';
import { Settings, Trash2 } from 'lucide-react';
import { ArrowData, Dict, DomainPerson } from '@/core/types';
import { PanelConfig } from '@/features/diagram-editor/types/panel';
import { NodeType } from '@dipeo/domain-models';
import { UNIFIED_NODE_CONFIGS, getPanelConfig } from '@/core/config';
import { GenericPropertyPanel } from '../renderers/GenericPropertyPanel';
import { useNodeOperations, useArrowOperations, usePersonOperations } from '@/features/diagram-editor/hooks';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { nodeId, arrowId, personId } from '@/core/types';

// Union type for all possible data types
type NodeData = Dict & { type: string };
export type UniversalData = NodeData | (ArrowData & { type: 'arrow' }) | (DomainPerson & { type: 'person' });

interface UniversalPropertiesPanelProps {
  nodeId: string;
  data: UniversalData;
}

export const UniversalPropertiesPanel: React.FC<UniversalPropertiesPanelProps> = React.memo(({ nodeId: entityId, data }) => {
  const nodeType = data.type;
  const nodeConfig = nodeType in UNIFIED_NODE_CONFIGS ? UNIFIED_NODE_CONFIGS[nodeType as keyof typeof UNIFIED_NODE_CONFIGS] : undefined;
  const { deleteNode } = useNodeOperations();
  const { deleteArrow } = useArrowOperations();
  const { deletePerson } = usePersonOperations();
  const { clearSelection } = useUnifiedStore();
  
  // Cast to a more permissive type that accepts the union
  const GenericPanel = GenericPropertyPanel as React.FC<{
    nodeId: string;
    data: Record<string, unknown>;
    config: PanelConfig<Record<string, unknown>>;
  }>;
  
  const panelConfig = getPanelConfig(nodeType as NodeType | 'arrow' | 'person');
  
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

  const handleDelete = () => {
    if (data.type === 'person') {
      deletePerson(personId(entityId));
    } else if (data.type === 'arrow') {
      deleteArrow(arrowId(entityId));
    } else {
      deleteNode(nodeId(entityId));
    }
    clearSelection();
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between border-b pb-2">
        <div className="flex items-center space-x-2">
          <span>{nodeConfig?.icon || '⚙️'}</span>
          <h3 className="text-lg font-semibold">
            {nodeConfig?.label ? `${nodeConfig.label} Properties` : `${nodeType} Properties`}
          </h3>
        </div>
        <button
          onClick={handleDelete}
          className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Delete"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
      <div className="space-y-4">
        <GenericPanel
          nodeId={entityId}
          data={data as Record<string, unknown>}
          config={panelConfig as PanelConfig<Record<string, unknown>>}
        />
      </div>
    </div>
  );
});

UniversalPropertiesPanel.displayName = 'UniversalPropertiesPanel';