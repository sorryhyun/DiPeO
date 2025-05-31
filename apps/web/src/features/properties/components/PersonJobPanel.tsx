import React from 'react';
import { type PersonJobBlockData } from '@/shared/types';
import { usePersons } from '@/shared/hooks/useStoreSelectors';
import { usePropertyPanel } from '@/features/properties';
import {
  Form, FormRow,
  InlineTextField, InlineSelectField, TextAreaField
} from '../wrappers';

export const PersonJobPanelContent: React.FC<{ nodeId: string; data: PersonJobBlockData }> = ({ nodeId, data }) => {
  const { persons } = usePersons();
  const { formData, handleChange } = usePropertyPanel<PersonJobBlockData>(nodeId, 'node', data);

  const forgetOptions = [
    { value: 'upon_request', label: 'Upon This Request' },
    { value: 'no_forget', label: 'Do Not Forget' },
    { value: 'on_every_turn', label: 'On Every Turn' }
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
              placeholder="Person Job"
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
            <InlineSelectField
              label="Forget"
              value={formData.contextCleaningRule || 'upon_request'}
              onChange={(v) => handleChange('contextCleaningRule', v as any)}
              options={forgetOptions}
              className="flex-1"
            />
            <InlineTextField
              label="Max Iter"
              value={String(formData.iterationCount || 1)}
              onChange={(v) => handleChange('iterationCount', parseInt(v) || 1)}
              placeholder="1"
              className="w-24"
            />
          </FormRow>
        </div>

        {/* Right column - Text properties */}
        <div className="space-y-4">
          <TextAreaField
            label="Default Prompt"
            value={formData.defaultPrompt || ''}
            onChange={(v) => handleChange('defaultPrompt', v)}
            rows={6}
            placeholder="Enter default prompt. Use {{variable_name}} for variables."
            hint={data.detectedVariables?.length ?
              `Detected variables: ${data.detectedVariables.map(v => `{{${v}}}`).join(', ')}` :
              undefined}
          />

          <TextAreaField
            label="First-Only Prompt"
            value={formData.firstOnlyPrompt || ''}
            onChange={(v) => handleChange('firstOnlyPrompt', v)}
            rows={4}
            placeholder="Prompt to use only on first execution."
          />
        </div>
      </div>
    </Form>
  );
};