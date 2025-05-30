import React from 'react';
import { Input } from '@repo/ui-kit';
import { useConsolidatedDiagramStore } from '@/stores';
import { type ArrowData } from '@repo/core-model';
import { usePropertyPanel } from '../hooks/usePropertyPanel';
import {
  Form, FormField, FormGrid,
  TextField, SelectField
} from '../wrappers';

export const ArrowPanelContent: React.FC<{ arrowId: string; data: ArrowData }> = ({ arrowId, data }) => {
  const { updateArrowData, arrows, nodes } = useConsolidatedDiagramStore();
  const { formData, handleChange: updateForm } = usePropertyPanel<ArrowData>(arrowId, 'arrow', data);

  const arrow = arrows.find(e => e.id === arrowId);
  const sourceNode = arrow ? nodes.find(n => n.id === arrow.source) : null;
  const isFromConditionNode = sourceNode?.type === 'conditionNode';
  const fixed = data.edgeKind === 'fixed';

  const handleChange = (field: keyof ArrowData, value: any) => {
    if (field === 'label' && formData.contentType === 'raw_text') {
      updateForm('label', value);
      updateForm('variableName', value);
      updateArrowData(arrowId, { label: value, variableName: value });
    } else {
      updateForm(field, value);
      updateArrowData(arrowId, { [field]: value });
    }
  };

  const contentTypeOptions = [
    ...(!fixed ? [
      { value: 'raw_text', label: 'Raw Text' },
      { value: 'variable_in_object', label: 'Variable in Object' }
    ] : []),
    { value: 'conversation_state', label: 'Conversation State' }
  ];

  return (
    <Form>
      <FormGrid columns={2}>
        <TextField
          label="Arrow Label"
          value={formData.label || ''}
          onChange={(v) => handleChange('label', v)}
          placeholder="e.g., user_query"
        />
        {!isFromConditionNode && (
          <SelectField
            label="Content Type"
            value={formData.contentType || (fixed ? 'whole' : 'raw_text')}
            onChange={(v) => handleChange('contentType', v as any)}
            options={contentTypeOptions}
            disabled={fixed}
          />
        )}
      </FormGrid>

      {formData.contentType === 'variable_in_object' && !isFromConditionNode && (
        <TextField
          label="Object Key Path"
          value={formData.objectKeyPath || ''}
          onChange={(v) => handleChange('objectKeyPath', v)}
          placeholder="e.g., user.name or data.items[0].value"
        />
      )}

      {data.sourceBlockId === data.targetBlockId && (
        <FormField label="Loop Radius">
          <Input
            type="number"
            min={10}
            value={formData.loopRadius ?? 30}
            onChange={(e) => handleChange('loopRadius', e.target.valueAsNumber)}
          />
        </FormField>
      )}
    </Form>
  );
};