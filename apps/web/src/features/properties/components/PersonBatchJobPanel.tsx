import React from 'react';
import { type PersonBatchJobBlockData } from '@/shared/types';
import { usePersons } from '@/shared/hooks/useStoreSelectors';
import { usePropertyPanel } from '@/features/properties';
import {
  Form, FormRow,
  InlineTextField, InlineSelectField, TextAreaField, CheckboxField
} from '../wrappers';

export const PersonBatchJobPanelContent: React.FC<{ nodeId: string; data: PersonBatchJobBlockData }> = ({ nodeId, data }) => {
  const { persons } = usePersons();
  const { formData, handleChange } = usePropertyPanel<PersonBatchJobBlockData>(nodeId, 'node', data);

  const aggregationOptions = [
    { value: 'concatenate', label: 'Concatenate' },
    { value: 'summarize', label: 'Summarize' },
    { value: 'custom', label: 'Custom' }
  ];

  const personOptions = persons.map(p => ({ value: p.id, label: p.label }));

  return (
    <Form>
      <div className="grid grid-cols-2 gap-4">
        {/* Left column - Option properties */}
        <div className="space-y-4">
          <FormRow>
            <InlineTextField
              label="Label"
              value={formData.label || ''}
              onChange={(v) => handleChange('label', v)}
              placeholder="Person Batch Job"
              className="flex-1"
            />
            <InlineSelectField
              label="Person"
              value={formData.personId || ''}
              onChange={(v) => handleChange('personId', v || undefined)}
              options={personOptions}
              placeholder="None"
              className="flex-1"
            />
          </FormRow>

          <FormRow>
            <InlineTextField
              label="Batch Size"
              value={String(formData.batchSize || 10)}
              onChange={(v) => handleChange('batchSize', parseInt(v) || 10)}
              placeholder="10"
              className="w-24"
            />
            <InlineTextField
              label="Max Iter"
              value={String(formData.iterationCount || 1)}
              onChange={(v) => handleChange('iterationCount', parseInt(v) || 1)}
              placeholder="1"
              className="w-24"
            />
          </FormRow>

          <CheckboxField
            label="Enable Parallel Processing"
            checked={formData.parallelProcessing || false}
            onChange={(v) => handleChange('parallelProcessing', v)}
          />

          <FormRow>
            <InlineSelectField
              label="Aggregation"
              value={formData.aggregationMethod || 'concatenate'}
              onChange={(v) => handleChange('aggregationMethod', v as any)}
              options={aggregationOptions}
              className="flex-1"
            />
          </FormRow>
        </div>

        {/* Right column - Text properties */}
        <div className="space-y-4">
          <TextAreaField
            label="Batch Prompt"
            value={formData.batchPrompt || ''}
            onChange={(v) => handleChange('batchPrompt', v)}
            rows={6}
            placeholder="Enter batch processing prompt. Use {{variable_name}} for variables."
            hint={data.detectedVariables?.length ?
              `Detected variables: ${data.detectedVariables.map(v => `{{${v}}}`).join(', ')}` :
              undefined}
          />

          {formData.aggregationMethod === 'custom' && (
            <TextAreaField
              label="Custom Aggregation Prompt"
              value={formData.customAggregationPrompt || ''}
              onChange={(v) => handleChange('customAggregationPrompt', v)}
              rows={4}
              placeholder="Enter custom aggregation prompt to process batch results."
            />
          )}
        </div>
      </div>
    </Form>
  );
};