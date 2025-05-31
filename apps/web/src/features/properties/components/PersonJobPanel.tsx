import React from 'react';
import { type PersonJobBlockData } from '@/shared/types';
import { usePropertyPanel } from '@/features/properties';
import {
  Form, TwoColumnPanelLayout, FormRow,
  LabelPersonRow, InlineSelectField, IterationCountField, VariableDetectionTextArea
} from '../wrappers';

export const PersonJobPanelContent: React.FC<{ nodeId: string; data: PersonJobBlockData }> = ({ nodeId, data }) => {
  const { formData, handleChange } = usePropertyPanel<PersonJobBlockData>(nodeId, 'node', data);

  const forgetOptions = [
    { value: 'upon_request', label: 'Upon This Request' },
    { value: 'no_forget', label: 'Do Not Forget' },
    { value: 'on_every_turn', label: 'On Every Turn' }
  ];

  return (
    <Form>
      <TwoColumnPanelLayout
        leftColumn={
          <>
            <LabelPersonRow
              labelValue={formData.label || ''}
              onLabelChange={(v) => handleChange('label', v)}
              personValue={formData.personId || ''}
              onPersonChange={(v) => handleChange('personId', v || undefined)}
              labelPlaceholder="Person Job"
            />

            <FormRow>
              <InlineSelectField
                label="Forget"
                value={formData.contextCleaningRule || 'upon_request'}
                onChange={(v) => handleChange('contextCleaningRule', v as any)}
                options={forgetOptions}
                className="flex-1"
              />
              <IterationCountField
                value={formData.iterationCount || 1}
                onChange={(v) => handleChange('iterationCount', v)}
              />
            </FormRow>
          </>
        }
        rightColumn={
          <>
            <VariableDetectionTextArea
              label="Default Prompt"
              value={formData.defaultPrompt || ''}
              onChange={(v) => handleChange('defaultPrompt', v)}
              rows={6}
              placeholder="Enter default prompt. Use {{variable_name}} for variables."
              detectedVariables={data.detectedVariables}
            />

            <VariableDetectionTextArea
              label="First-Only Prompt"
              value={formData.firstOnlyPrompt || ''}
              onChange={(v) => handleChange('firstOnlyPrompt', v)}
              rows={4}
              placeholder="Prompt to use only on first execution."
            />
          </>
        }
      />
    </Form>
  );
};