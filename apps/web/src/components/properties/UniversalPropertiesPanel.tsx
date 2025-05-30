import React from 'react';
import { useConsolidatedDiagramStore } from '@/stores';
import { usePropertyForm as usePropertyFormBase } from '@repo/diagram-ui';
import { Settings } from 'lucide-react';
import { Panel, Form } from '@repo/properties-ui';
import { UNIFIED_NODE_CONFIGS } from '@repo/core-model';
import { usePersons } from '@/hooks/useStoreSelectors';
import { renderField } from './fieldRenderers';

// Create a wrapper that connects to the store
function usePropertyForm<T extends Record<string, any>>(
  nodeId: string,
  initialData: T
) {
  const updateNodeData = useConsolidatedDiagramStore(state => state.updateNodeData);
  return usePropertyFormBase(initialData, (updates) => {
    updateNodeData(nodeId, updates);
  });
}

export const UniversalPropertiesPanel: React.FC<{ nodeId: string; data: any }> = ({ nodeId, data }) => {
  const nodeType = data.type;
  const config = UNIFIED_NODE_CONFIGS[nodeType];
  const { persons } = usePersons();
  const { formData, handleChange } = usePropertyForm(nodeId, data);
  
  if (!config) {
    return (
      <Panel icon={<Settings className="w-5 h-5" />} title="Unknown Node Type">
        <div className="text-red-500">No configuration found for node type: {nodeType}</div>
      </Panel>
    );
  }

  return (
    <Panel icon={<span>{config.emoji}</span>} title={config.propertyTitle}>
      <Form>
        <div className="space-y-4">
          {config.propertyFields.map((field) => 
            renderField(field, formData, handleChange, { persons, data })
          )}
        </div>
      </Form>
    </Panel>
  );
};