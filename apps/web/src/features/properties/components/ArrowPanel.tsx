import React from 'react';
import { Input } from '@/shared/components';
import { useConsolidatedDiagramStore } from '@/shared/stores';
import { type ArrowData } from '@/shared/types';
import { usePropertyPanel } from '@/features/properties';
import { useArrowDataUpdater } from '@/shared/hooks/useStoreSelectors';
import {
  Form,
  FormField,
  TwoColumnPanelLayout,
  TextField,
  SelectField
} from './ui-components/FormComponents';

export const ArrowPanelContent: React.FC<{ arrowId: string; data: ArrowData }> = ({ arrowId, data }) => {
  const updateArrowData = useArrowDataUpdater();
  const arrow = useConsolidatedDiagramStore(state => state.arrows.find(e => e.id === arrowId));
  const sourceNode = useConsolidatedDiagramStore(state => 
    arrow ? state.nodes.find(n => n.id === arrow.source) : null
  );
  const { formData, handleChange: updateForm } = usePropertyPanel<ArrowData>(arrowId, 'arrow', data);

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
      <TwoColumnPanelLayout
        leftColumn={
          <>
            <TextField
              label="Arrow Label"
              value={formData.label || ''}
              onChange={(v) => handleChange('label', v)}
              placeholder="e.g., user_query"
            />
            {formData.contentType === 'variable_in_object' && !isFromConditionNode && (
              <TextField
                label="Object Key Path"
                value={formData.objectKeyPath || ''}
                onChange={(v) => handleChange('objectKeyPath', v)}
                placeholder="e.g., user.name or data.items[0].value"
              />
            )}
          </>
        }
        rightColumn={
          <>
            {!isFromConditionNode && (
              <SelectField
                label="Content Type"
                value={formData.contentType || (fixed ? 'whole' : 'raw_text')}
                onChange={(v) => handleChange('contentType', v as 'raw_text' | 'variable_in_object' | 'conversation_state')}
                options={contentTypeOptions}
                disabled={fixed}
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
          </>
        }
      />
    </Form>
  );
};