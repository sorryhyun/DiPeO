import React from 'react';
import { type PersonBatchJobBlockData } from '@/shared/types';
import { usePropertyPanel } from '@/features/properties';
import {
  Form, TwoColumnPanelLayout, FormRow,
  LabelPersonRow, InlineTextField, InlineSelectField, IterationCountField,
  VariableDetectionTextArea, CheckboxField
} from '../wrappers';

export const PersonBatchJobPanelContent: React.FC<{ nodeId: string; data: PersonBatchJobBlockData }> = ({ nodeId, data }) => {
  const { formData, handleChange } = usePropertyPanel<PersonBatchJobBlockData>(nodeId, 'node', data);

  const aggregationOptions = [
    { value: 'concatenate', label: 'Concatenate' },
    { value: 'summarize', label: 'Summarize' },
    { value: 'custom', label: 'Custom' }
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
              labelPlaceholder="Person Batch Job"
            />

            <FormRow>
              <InlineTextField
                label="Batch Size"
                value={String(formData.batchSize || 10)}
                onChange={(v) => handleChange('batchSize', parseInt(v) || 10)}
                placeholder="10"
                className="w-24"
              />
              <IterationCountField
                value={formData.iterationCount || 1}
                onChange={(v) => handleChange('iterationCount', v)}
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
          </>
        }
        rightColumn={
          <>
            <VariableDetectionTextArea
              label="Batch Prompt"
              value={formData.batchPrompt || ''}
              onChange={(v) => handleChange('batchPrompt', v)}
              rows={6}
              placeholder="Enter batch processing prompt. Use {{variable_name}} for variables."
              detectedVariables={data.detectedVariables}
            />

            {formData.aggregationMethod === 'custom' && (
              <VariableDetectionTextArea
                label="Custom Aggregation Prompt"
                value={formData.customAggregationPrompt || ''}
                onChange={(v) => handleChange('customAggregationPrompt', v)}
                rows={4}
                placeholder="Enter custom aggregation prompt to process batch results."
              />
            )}
          </>
        }
      />
    </Form>
  );
};