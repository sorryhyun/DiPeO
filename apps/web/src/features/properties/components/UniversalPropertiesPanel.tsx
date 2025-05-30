import React from 'react';
import { Settings } from 'lucide-react';
import { Panel, Form, usePropertyForm } from '../wrappers';
import { UNIFIED_NODE_CONFIGS } from '@/shared/types';
import { usePersons } from '@/shared/hooks/useStoreSelectors';
import { renderInlineField, renderTextAreaField, isTextAreaField } from '@/features/properties';


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

  const inlineFields = config.propertyFields.filter(field => !isTextAreaField(field));
  const textAreaFields = config.propertyFields.filter(field => isTextAreaField(field));

  return (
    <Panel icon={<span>{config.emoji}</span>} title={config.propertyTitle}>
      <Form>
        <div className="grid grid-cols-2 gap-4">
          {/* Left column - Horizontal arrangement of other fields */}
          <div className="space-y-4">
            {inlineFields.map((field) => 
              renderInlineField(field, formData, handleChange, { persons, data })
            )}
          </div>

          {/* Right column - Text areas */}
          <div className="space-y-4">
            {textAreaFields.map((field) => 
              renderTextAreaField(field, formData, handleChange, { persons, data })
            )}
          </div>
        </div>
      </Form>
    </Panel>
  );
};